import os
import requests
import json
import threading
import logging
import time
import asyncio
import aiohttp
import re
from threading import Lock
from typing import Dict, Any, Optional, List, Literal, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dataclasses import dataclass, field


from pydantic import BaseModel, Field, ValidationError, field_validator

try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    load_dotenv(find_dotenv(usecwd=True), override=False)
except Exception:
    # Safe fallback when python-dotenv is not installed
    pass

logger = logging.getLogger(__name__)

# Version tag for prompt templates; bump when changing prompt shape materially
PROMPT_VERSION = "v1"

# Translation table to normalize curly quotes and apostrophes
_SMART_QUOTE_TRANSLATION = str.maketrans({
    "“": '"',
    "”": '"',
    "„": '"',
    "‟": '"',
    "’": "'",
    "‘": "'",
    "‚": "'",
    "‛": "'",
})


def _normalize_unicode_quotes(text: str) -> str:
    """Replace curly quotes/apostrophes with ASCII equivalents."""
    if not text:
        return text
    return text.translate(_SMART_QUOTE_TRANSLATION)


def _escape_control_chars_inside_strings(text: str) -> str:
    """
    Escape raw newline/tab characters that may appear inside quoted strings.

    Some frontier models occasionally emit literal newlines within JSON strings.
    Python's json module rejects these as invalid, so we proactively escape them.
    """
    if not text:
        return text

    escaped: List[str] = []
    in_string = False
    escape = False
    replacements = {
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
    }

    for ch in text:
        if ch == '"' and not escape:
            in_string = not in_string
            escaped.append(ch)
            continue

        if in_string and ch in replacements:
            escaped.append(replacements[ch])
            escape = False
            continue

        escaped.append(ch)
        if ch == "\\" and not escape:
            escape = True
        else:
            escape = False

    return "".join(escaped)


def _clean_json_text(text: str) -> str:
    """Normalize unicode quotes and escape control chars inside JSON strings."""
    text = _normalize_unicode_quotes(text)
    text = _escape_control_chars_inside_strings(text)
    return text


def _get_cfg(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Resolve configuration from environment variables (optionally populated by .env).

    This helper only reads from the current process environment; it does not
    itself cache or persist secrets. Callers may still store returned values
    in memory (for example on a client instance).

    Resolution order:
    1. Environment variable with the given name
    2. Provided default value (if any)

    Args:
        name: Configuration variable name (e.g., 'OPENROUTER_API_KEY').
        default: Default to use if the variable is not set.

    Returns:
        The configuration value or the default.
    """
    val = os.getenv(name)
    if val is not None and val != "":
        return val
    return default


class AIResponse(BaseModel):
    """Strict schema for AI enrichment output."""
    priority: Literal['critical', 'high', 'medium', 'low'] = Field(default='medium')
    user_impact: str = ""
    fix_suggestion: List[str] = Field(default_factory=list)
    effort_minutes: int = 15
    effort_rationale: Optional[str] = None

    # Optional, richer fields for future UI enhancements
    code_example: Optional[str] = None
    wcag_refs: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    test_steps: List[str] = Field(default_factory=list)
    automation_hints: List[str] = Field(default_factory=list)
    personas_impact: Optional[Dict[str, str]] = None
    root_cause_hypothesis: Optional[str] = None
    component_guess: Optional[str] = None
    # Free-form per-selector or per-element plan items
    fix_plan: List[Dict[str, Any]] = Field(default_factory=list)
    ticket_title: Optional[str] = None
    ticket_body: Optional[str] = None
    confidence: Optional[int] = None
    risk_level: Optional[str] = None

    @field_validator("fix_suggestion", mode="before")
    @classmethod
    def coerce_fix_suggestion(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            normalized = v.replace("\r", "")
            parts = [part.strip(" •-\t") for part in normalized.split("\n")]
            cleaned = [part for part in parts if part]
            if cleaned:
                return cleaned
            stripped = normalized.strip()
            return [stripped] if stripped else []
        return [str(v)]

    @field_validator("fix_plan", mode="before")
    @classmethod
    def coerce_fix_plan(cls, v: Any) -> List[Dict[str, Any]]:
        if v is None:
            return []
        if isinstance(v, dict):
            # AI sometimes returns a single object with approach/avoid/etc.
            return [v]
        if isinstance(v, list):
            out: List[Dict[str, Any]] = []
            for item in v:
                if isinstance(item, dict):
                    out.append(item)
                else:
                    out.append({"step": str(item)})
            return out
        return [{"step": str(v)}]

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    @field_validator("fix_suggestion", mode="after")
    @classmethod
    def validate_quality(cls, v: List[str]) -> List[str]:
        """Ensure fix suggestions meet quality standards (warn but don't reject)."""
        if not v:
            return ["Contact accessibility team for specific guidance"]

        for suggestion in v:
            if suggestion is None:
                continue
            if len(str(suggestion).strip()) < 10:
                logger.warning(f"Very short fix suggestion: {str(suggestion)[:50]}")

        return v


@dataclass
class UsageStats:
    """Track token usage and cost metrics with persistent storage"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    _stats_file: str = field(default=".ai_usage_stats.json", init=False, repr=False)
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int, cost: float = 0.0):
        """Add usage from a single API call"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += (prompt_tokens + completion_tokens)
        self.estimated_cost_usd += cost
        self._save()
    
    def add_failure(self):
        """Record a failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self._save()
    
    def _save(self):
        """Save stats to file"""
        try:
            with open(self._stats_file, 'w') as f:
                json.dump(self.to_dict(), f)
        except Exception as e:
            logger.warning(f"Failed to save usage stats: {e}")
    
    @classmethod
    def load(cls, stats_file: str = ".ai_usage_stats.json") -> 'UsageStats':
        """Load stats from file or create new if not exists"""
        try:
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                    stats = cls(
                        total_requests=data.get('total_requests', 0),
                        successful_requests=data.get('successful_requests', 0),
                        failed_requests=data.get('failed_requests', 0),
                        total_prompt_tokens=data.get('total_prompt_tokens', 0),
                        total_completion_tokens=data.get('total_completion_tokens', 0),
                        total_tokens=data.get('total_tokens', 0),
                        estimated_cost_usd=data.get('estimated_cost_usd', 0.0)
                    )
                    stats._stats_file = stats_file
                    return stats
        except Exception as e:
            logger.warning(f"Failed to load usage stats: {e}")
        
        stats = cls()
        stats._stats_file = stats_file
        return stats
    
    def reset(self):
        """Reset all stats to zero"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.estimated_cost_usd = 0.0
        self._save()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/API responses"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "success_rate": round(self.successful_requests / self.total_requests * 100, 2) if self.total_requests > 0 else 0.0
        }


class SimpleAIClient:
    """
    Enhanced AI client for OpenRouter with better error handling and prompts
    Optimized for Mistral Devstral and other free models
    """

    def __init__(self):
        self.api_key = _get_cfg('OPENROUTER_API_KEY')
        self.base_url = _get_cfg('OPENROUTER_BASE_URL', "https://openrouter.ai/api/v1")
        self.model = _get_cfg('OPENROUTER_MODEL', "mistralai/devstral-2512:free")  # Default model
        try:
            self.timeout = int(_get_cfg('OPENROUTER_TIMEOUT', "30") or "30")
        except ValueError:
            self.timeout = 30

        # Rate limiting setup
        self._rate_limiter = Lock()
        self._last_call_time = 0.0
        self._min_interval = 0.2  # 200ms between calls = max 5 requests/second
        
        # Usage tracking - load from persistent storage
        self.usage_stats = UsageStats.load()
        self._usage_lock = Lock()
        
        # Pricing per 1M tokens (update these based on your model)
        # For free models, these will be 0
        self.price_per_1m_prompt_tokens = 0.0
        self.price_per_1m_completion_tokens = 0.0
        
        # Model-specific settings (will be configured below)
        self.max_tokens = 800
        self.temperature = 0.1
        self.supports_json_mode = False
        
        # Setup session with retry logic
        self.session = requests.Session()
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,  # Maximum 3 retries
            backoff_factor=1,  # Wait 1s, 2s, 4s between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
            allowed_methods=["POST"],  # Only retry POST requests
            raise_on_status=False  # Don't raise exception, let us handle it
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Apply model-specific configuration
        self._configure_for_model()

        if not self.api_key:
            logger.warning("OpenRouter API key not found. AI features will be disabled.")
        else:
            logger.info(f"AI Client initialized with {self.model} (rate limiting + usage tracking enabled)")

    def _configure_for_model(self):
        """Apply model-specific settings for optimal JSON generation"""
        model_lower = self.model.lower()
        
        if "mistral" in model_lower or "devstral" in model_lower:
            # Mistral needs explicit instructions and more tokens
            self.max_tokens = 1200
            self.temperature = 0.0  # Very deterministic for JSON
            self.supports_json_mode = False
            logger.info("✓ Configured for Mistral/Devstral model")
        
        elif "deepseek" in model_lower:
            self.max_tokens = 800
            self.temperature = 0.2
            self.supports_json_mode = False
            logger.warning("⚠ DeepSeek can produce malformed JSON - consider switching to Mistral")
        
        elif "gpt" in model_lower:
            self.max_tokens = 800
            self.temperature = 0.1
            self.supports_json_mode = True
            logger.info("✓ Configured for GPT model with JSON mode")
        
        else:
            # Safe defaults for unknown models
            self.max_tokens = 800
            self.temperature = 0.1
            self.supports_json_mode = False
            logger.info(f"Using default configuration for model: {self.model}")

    @property
    def prompt_version(self) -> str:
        """Version tag for prompt templates to help cache fingerprinting."""
        return PROMPT_VERSION

    def is_available(self) -> bool:
        """Check if AI service is available"""
        return bool(self.api_key)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return self.usage_stats.to_dict()
    
    def reset_usage_stats(self):
        """Reset usage statistics (useful for testing or new sessions)"""
        self.usage_stats.reset()
        logger.info("Usage statistics reset")

    def analyze_accessibility_issue(self, issue_description: str, elements: Optional[list] = None, impact: Optional[str] = None, rule_id: Optional[str] = None, framework: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Comprehensive AI analysis for accessibility issues
        Returns: priority, user_impact, fix_suggestion, code_example, effort_minutes
        """
        if not self.is_available():
            return None
            
        # If caller didn't provide element_count, infer from elements list
        element_count = None
        if element_count is None and elements and isinstance(elements, list):
            element_count = len(elements)

        prompt = self._build_comprehensive_prompt(issue_description, elements, impact, rule_id, framework, element_count)

        try:
            response = self._make_api_call(prompt)
            if response:
                return self._parse_ai_response(response)
            return None

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None

    def _build_comprehensive_prompt(
        self,
        issue_description: str,
        elements: Optional[list],
        impact: Optional[str] = None,
        rule_id: Optional[str] = None,
        framework: Optional[str] = None,
        element_count: Optional[int] = None,
    ) -> str:
        """
        Build a strict, developer-friendly prompt.
        Key rules:
          - Never invent data (colors, ratios, user percentages, file locations).
          - Prefer evidence-based fixes using provided context.
          - Provide actionable steps + acceptance criteria + verification.
        """
        framework_norm = (framework or "html").lower()
        impact_text = f"Impact level: {impact}" if impact else "Impact level: unknown"

        # Format element context for the prompt
        elements_text = self._format_elements_for_prompt(elements, rule_id)

        # Try to detect occurrence_count from merged metadata (if present)
        occurrences = None
        if isinstance(elements, list) and elements and isinstance(elements[0], dict) and "occurrence_count" in elements[0]:
            try:
                occurrences = int(elements[0].get("occurrence_count") or 0) or None
            except (TypeError, ValueError):
                occurrences = None

        occ_text = f"Occurrences (grouped): {occurrences}" if occurrences else ""

        # Add compact rule knowledge if available
        kb = self._get_rule_knowledge(rule_id, framework_norm)
        kb_text = ""
        if kb:
            kb_text = (
                f"Rule ID: {kb.get('rule_id')}\n"
                f"Relevant WCAG: {', '.join(kb.get('wcag_refs', []))}\n"
                f"Common causes: {', '.join(kb.get('common_causes', []))}\n"
                f"Guidance ({framework_norm}): {kb.get('guidance', '')}\n"
                f"Example ({framework_norm}): {kb.get('example', '')}\n"
            )

        # High-quality example WITHOUT fake precision or invented values
        example_json = {
            "priority": "high",
            "user_impact": "Screen reader users may not be able to identify the control’s purpose, blocking interaction.",
            "fix_suggestion": [
                "If the control is icon-only, add an accessible name (aria-label) that describes the action (e.g., \"Close dialog\", \"Next slide\").",
                "If visible text is appropriate, add descriptive text content inside the element.",
                "If an on-screen label already exists, reference it using aria-labelledby."
            ],
            "effort_minutes": 10,
            "code_example": "<button aria-label=\"Close dialog\">✕</button>",
            "wcag_refs": ["4.1.2", "2.5.3"],
            "acceptance_criteria": [
                "The element exposes a non-empty accessible name in the Accessibility Tree.",
                "A screen reader announces the element name and role (e.g., “Close dialog, button”).",
                "The issue is no longer reported by the scanner for the same page state."
            ],
            "test_steps": [
                "Open Chrome DevTools → Elements → Accessibility and confirm the Name is populated.",
                "Navigate with keyboard (Tab/Shift+Tab) and confirm focus order is correct.",
                "Test with a screen reader (NVDA/VoiceOver): focus the control and confirm the announced label matches its action."
            ],
            "automation_hints": [
                "Add an assertion that the element has a non-empty accessible name (e.g., aria-label or textContent)."
            ],
            "root_cause_hypothesis": "Element has no visible text and no ARIA labeling attributes.",
            "component_guess": "IconButton / carousel control / dialog close button",
            "fix_plan": [
                {
                    "approach": "Choose ONE: visible text, aria-label, or aria-labelledby (preferred if on-screen label exists).",
                    "avoid": [
                        "Do not use aria-label that repeats nearby visible text unless necessary.",
                        "Do not use generic labels like \"button\"."
                    ]
                }
            ],
            "ticket_title": "Add accessible name to unlabeled button",
            "ticket_body": "One or more buttons are missing an accessible name. Add visible text or ARIA labeling so assistive technologies can identify the action.",
            "confidence": 80,
            "risk_level": "low"
        }

        prompt = (
            "CRITICAL INSTRUCTION: Return ONLY valid JSON. No markdown. No commentary.\n\n"
            "You are a senior accessibility engineer writing developer-ready remediation guidance.\n\n"
            "ISSUE INPUT:\n"
            f"- Issue description: {issue_description}\n"
            f"- {impact_text}\n"
            f"- Rule ID: {rule_id or 'unknown'}\n"
            f"- Framework: {framework_norm}\n"
            f"- {occ_text}\n\n"
            f"{elements_text}\n\n"
            "RULE KNOWLEDGE (if available):\n"
            f"{kb_text if kb_text else 'None'}\n\n"
            "STRICT RULES (DO NOT VIOLATE):\n"
            "1) DO NOT invent numbers, user percentages, file locations, colors, or contrast ratios.\n"
            "2) If the scanner did NOT provide foreground/background colors or a recommended color, DO NOT output hex values.\n"
            "   - For contrast, provide process-based guidance (adjust token, verify with checker) and validation steps.\n"
            "3) DO NOT guess labels like \"Search\" unless the context clearly indicates it.\n"
            "   - If action is unknown, use a placeholder pattern: \"<ACTION>\" and tell dev to set the correct action label.\n"
            "4) Make suggestions specific to the provided HTML/context when possible.\n"
            "5) Output must be concise but actionable for a developer.\n\n"
            "OUTPUT JSON SCHEMA (must include these keys):\n"
            "{\n"
            "  \"priority\": \"critical|high|medium|low\",\n"
            "  \"user_impact\": \"...\",\n"
            "  \"fix_suggestion\": [\"...\"],\n"
            "  \"effort_minutes\": 1,\n"
            "  \"code_example\": \"...\" | null,\n"
            "  \"wcag_refs\": [\"...\"],\n"
            "  \"acceptance_criteria\": [\"...\"],\n"
            "  \"test_steps\": [\"...\"],\n"
            "  \"automation_hints\": [\"...\"],\n"
            "  \"root_cause_hypothesis\": \"...\" | null,\n"
            "  \"component_guess\": \"...\" | null,\n"
            "  \"fix_plan\": [ { ... } ] | null,\n"
            "  \"ticket_title\": \"...\" | null,\n"
            "  \"ticket_body\": \"...\" | null,\n"
            "  \"confidence\": 0,\n"
            "  \"risk_level\": \"low|medium|high\" | null\n"
            "}\n\n"
            f"EXAMPLE OUTPUT (style reference only):\n{json.dumps(example_json, indent=2)}\n\n"
            f"Prompt-Version: {PROMPT_VERSION}\n\n"
            "NOW RETURN ONLY THE JSON OBJECT FOR THE ISSUE INPUT ABOVE:"
        )

        return prompt

    def _format_elements_for_prompt(self, elements: Optional[list], rule_id: Optional[str]) -> str:
        """Format element context for the prompt.

        Accepts list of selectors (strings) or list of dicts with keys like
        'selector', 'html', 'tag', 'role', 'aria_label', 'fg_color', 'bg_color', 'contrast_ratio'.
        Returns a readable, truncated text block for inclusion in prompts.
        """
        if not elements:
            return "AFFECTED SELECTORS: []"

        # If elements is a dict-like wrapper, try to extract inner list
        if isinstance(elements, dict) and elements.get("elements"):
            elems = elements.get("elements")
        else:
            elems = elements

        if not isinstance(elems, list):
            try:
                return f"AFFECTED SELECTORS: {str(elems)}"
            except Exception:
                return "AFFECTED SELECTORS: []"

        meta_occurrences = None
        # If the analyzer merged occurrences, it may prepend a synthetic meta dict:
        #   {"occurrence_count": N}
        # Remove it from the element list and expose count to the prompt.
        if isinstance(elems, list) and elems and isinstance(elems[0], dict) and ("occurrence_count" in elems[0]) and (len(elems[0].keys()) == 1):
            try:
                raw_count = elems[0].get("occurrence_count")

                meta_occurrences = int(raw_count) if isinstance(raw_count, (int, str)) else 1
            except Exception:
                meta_occurrences = None
            elems = elems[1:]

        lines = ["AFFECTED ELEMENTS (showing up to 5):"]
        if meta_occurrences:
            lines.append(f"Total occurrences in report: {meta_occurrences}")
        for i, node in enumerate(elems[:5], 1):
            if isinstance(node, dict):
                selector = node.get('selector') or node.get('target') or 'unknown-selector'
                # defensive sanitize
                try:
                    selector = str(selector)
                    if not selector or selector.lower() in ('none', 'undefined'):
                        selector = 'unknown-selector'
                except Exception:
                    selector = 'unknown-selector'

                html = node.get('html') or ''
                tag = node.get('tag') or self._extract_tag_from_html(html) or 'unknown'
                role = node.get('role') or node.get('current_role') or 'none'
                aria = node.get('aria_label') or node.get('aria-label') or 'none'

                lines.append(f"\nElement {i}:")
                lines.append(f"  Selector: {selector}")
                lines.append(f"  Tag: <{tag}>")
                if html:
                    snippet = (html[:200] + '...') if len(html) > 200 else html
                    lines.append(f"  HTML: {snippet}")

                if 'fg_color' in node or 'contrast_ratio' in node:
                    fg = node.get('fg_color') or node.get('fgColor') or 'unknown'
                    bg = node.get('bg_color') or node.get('bgColor') or 'unknown'
                    ratio = str(node.get('contrast_ratio') or node.get('contrastRatio') or 'unknown')
                    lines.append(f"  Current colors: {fg} on {bg} (contrast: {ratio})")
                    exp = node.get("expected_ratio") or node.get("expectedContrastRatio")
                    if exp is not None:
                        lines.append(f"  Expected contrast: {exp}:1")
                    rec = node.get("recommended_text_color")
                    if rec:
                        lines.append(f"  Tool recommended text color: {rec}")

                lines.append(f"  Role: {role}")
                lines.append(f"  ARIA label: {aria}")
            else:
                # simple selector string
                try:
                    sel = str(node)
                except Exception:
                    sel = 'unknown-selector'
                if not sel or sel.lower() in ('none', 'undefined'):
                    sel = 'unknown-selector'
                lines.append(f"\nElement {i}: Selector: {sel}")

        if len(elems) > 5:
            lines.append(f"\n... and {len(elems)-5} more elements")

        return "\n".join(lines)

    def _extract_tag_from_html(self, html: str) -> Optional[str]:
        """Return the tag name from an HTML fragment, or None."""
        if not html:
            return None
        try:
            m = re.match(r"\s*<\s*(\w+)", html)
            if m:
                return m.group(1).lower()
        except Exception:
            return None
        return None
    

    def _get_rule_knowledge(self, rule_id: Optional[str], framework: str) -> Optional[Dict[str, Any]]:
        """Return compact, framework-aware guidance for common rules."""
        if not rule_id:
            return None
        rid = str(rule_id).lower()
        kb_map: Dict[str, Dict[str, Any]] = {
            "button-name": {
                "wcag_refs": ["WCAG 4.1.2"],
                "common_causes": [
                    "Icon-only buttons without aria-label",
                    "Clickable divs/spans without role/button and name",
                ],
                "guidance_by_framework": {
                    "html": "Use visible text or aria-label; avoid bare <div> as buttons.",
                    "react": "Provide children text or aria-label on <button>; avoid onClick on <div>.",
                },
                "example_by_framework": {
                    "html": "<button aria-label=\"Search\"><span class=\"icon\"></span></button>",
                    "react": "<button aria-label=\"Search\"><Icon /></button>",
                },
            },
            "image-alt": {
                "wcag_refs": ["WCAG 1.1.1"],
                "common_causes": ["Missing alt on informative images", "Decorative images with empty alt not used"],
                "guidance_by_framework": {
                    "html": "Provide meaningful alt for informative images; use alt=\"\" for decorative.",
                    "react": "On <img>, set alt. For background/decorative, ensure it's ignored by AT.",
                },
                "example_by_framework": {
                    "html": "<img src=\"product.jpg\" alt=\"Red shoes, front view\">",
                    "react": "<img src=\"/logo.png\" alt=\"Acme Corp\" />",
                },
            },
            "label": {
                "wcag_refs": ["WCAG 3.3.2"],
                "common_causes": ["Inputs without <label>", "Placeholder used as label"],
                "guidance_by_framework": {
                    "html": "Associate <label for> with input id; ensure visible label.",
                    "react": "Use <label htmlFor=...> and input id; don't rely on placeholder.",
                },
                "example_by_framework": {
                    "html": "<label for=\"email\">Email</label><input id=\"email\">",
                    "react": "<label htmlFor=\"email\">Email</label><input id=\"email\" />",
                },
            },
            "color-contrast": {
                "wcag_refs": ["WCAG 1.4.3"],
                "common_causes": ["Text on brand colors below 4.5:1", "Disabled buttons with low contrast"],
                "guidance_by_framework": {
                    "html": "Adjust colors to meet 4.5:1 normal text or 3:1 large text.",
                    "react": "Use design tokens; ensure tokens meet 4.5:1/3:1 contrast.",
                },
                "example_by_framework": {
                    "html": "Use #1F2937 text on #FFFFFF background for 12pt text.",
                    "react": "Apply theme variable with sufficient contrast (e.g., text-primary on bg-base).",
                },
            },
            "link-name": {
                "wcag_refs": ["WCAG 2.4.4"],
                "common_causes": ["Links with 'click here' or icon-only without name", "SVG/icon links lacking aria-label"],
                "guidance_by_framework": {
                    "html": "Link text should describe destination; for icon-only, add aria-label or aria-labelledby.",
                    "react": "Provide meaningful children on <a> or aria-label; avoid ambiguous link text.",
                },
                "example_by_framework": {
                    "html": "<a href=\"/account\">Account settings</a>",
                    "react": "<a href=\"/cart\" aria-label=\"View shopping cart\"><CartIcon /></a>",
                },
            },
            "focus-visible": {
                "wcag_refs": ["WCAG 2.4.7"],
                "common_causes": ["Outline removed via CSS", "Custom components without visible focus styles"],
                "guidance_by_framework": {
                    "html": "Ensure a visible focus indicator (:focus or :focus-visible); don't remove outlines.",
                    "react": "Provide focus styles for interactive components; use :focus-visible or focus ring utilities.",
                },
                "example_by_framework": {
                    "html": "button:focus-visible{outline:2px solid #2563EB; outline-offset:2px;}",
                    "react": "<button className=\"focus:outline-blue-600 focus:outline-2\">Save</button>",
                },
            },
            "heading-order": {
                "wcag_refs": ["WCAG 1.3.1"],
                "common_causes": ["Skipping heading levels", "Using headings for styling instead of structure"],
                "guidance_by_framework": {
                    "html": "Use hierarchical h1–h6 without skipping; use CSS for styling instead of incorrect levels.",
                    "react": "Render correct <h*> levels based on section depth; avoid jumping from h1 to h3.",
                },
                "example_by_framework": {
                    "html": "<h1>Products</h1>\n<h2>Shoes</h2>\n<h3>Running</h3>",
                    "react": "<h1>Docs</h1><h2>Getting Started</h2>",
                },
            },
            "page-has-heading-one": {
                "wcag_refs": ["WCAG 1.3.1", "Best Practice"],
                "common_causes": ["No primary page heading (h1)", "Logo used instead of heading"],
                "guidance_by_framework": {
                    "html": "Ensure one descriptive <h1> per page near the top.",
                    "react": "Include a top-level <h1> describing the page purpose.",
                },
                "example_by_framework": {
                    "html": "<h1>Order Confirmation</h1>",
                    "react": "<h1>Dashboard</h1>",
                },
            },
            "landmark-one-main": {
                "wcag_refs": ["WCAG 1.3.1", "WCAG 2.4.1"],
                "common_causes": ["Missing <main> landmark", "Multiple main regions"],
                "guidance_by_framework": {
                    "html": "Use a single <main> for primary content; header/footer/nav as appropriate.",
                    "react": "Wrap page content in <main>; ensure only one main landmark.",
                },
                "example_by_framework": {
                    "html": "<main id=\"main\">...content...</main>",
                    "react": "<main role=\"main\">{children}</main>",
                },
            },
            "region": {
                "wcag_refs": ["WCAG 1.3.1", "WCAG 2.4.1"],
                "common_causes": ["Landmarks missing labels when multiple of same type", "Overuse of generic containers"],
                "guidance_by_framework": {
                    "html": "Label multiple nav/aside regions with aria-label; use semantic elements.",
                    "react": "For repeated landmarks, set aria-label (e.g., aria-label=\"Primary\").",
                },
                "example_by_framework": {
                    "html": "<nav aria-label=\"Primary\">...</nav>",
                    "react": "<nav aria-label=\"Footer links\">...</nav>",
                },
            },
        }
        # Additional detailed rules
        kb_map.update({
            "identical-links-same-purpose": {
                "wcag_refs": ["WCAG 2.4.9", "WCAG 2.4.4"],
                "common_causes": [
                    "Multiple 'Home' or 'Back' links without context",
                    "Same link text in header and footer pointing to different pages",
                    "Icon-only links without unique aria-labels"
                ],
                "guidance_by_framework": {
                    "html": "Add aria-label to differentiate links OR change visible text to include context",
                    "react": "Use aria-label prop or wrap link text with contextual information",
                },
                "example_by_framework": {
                    "html": (
                        "<!-- BEFORE: Two 'Home' links, different purposes -->\n"
                        "<nav><a href='/'>Home</a></nav>\n"
                        "<footer><a href='/'>Home</a></footer>\n\n"
                        "<!-- AFTER: Differentiated with aria-label -->\n"
                        "<nav><a href='/' aria-label='Home - Main navigation'>Home</a></nav>\n"
                        "<footer><a href='/' aria-label='Return to homepage'>Home</a></footer>"
                    ),
                    "react": (
                        "// BEFORE\n"
                        "<Link to='/'>Home</Link>\n\n"
                        "// AFTER\n"
                        "<Link to='/' aria-label='Home - Main navigation'>Home</Link>"
                    ),
                },
                "developer_tips": [
                    "If links go to SAME destination with SAME purpose, this is usually fine",
                    "Only add differentiation when links have DIFFERENT purposes or contexts",
                    "Consider using visually hidden text instead of aria-label for better SEO"
                ]
            },
            "listitem": {
                "wcag_refs": ["WCAG 1.3.1", "WCAG 4.1.2"],
                "common_causes": [
                    "Carousel/slider items not wrapped in <ul>/<ol>",
                    "Custom list styling using <div> instead of <li>",
                    "JavaScript-generated content missing semantic markup"
                ],
                "guidance_by_framework": {
                    "html": "Wrap repeating items in <ul> and each item in <li>. Preserve existing classes.",
                    "react": "Return <ul> with <li> children. Keep carousel functionality intact.",
                },
                "example_by_framework": {
                    "html": (
                        "<!-- BEFORE: Non-semantic carousel -->\n"
                        "<div class='carousel'>\n"
                        "  <div class='orbit-slide'>Slide 1</div>\n"
                        "  <div class='orbit-slide'>Slide 2</div>\n"
                        "</div>\n\n"
                        "<!-- AFTER: Semantic carousel -->\n"
                        "<div class='carousel'>\n"
                        "  <ul>\n"
                        "    <li class='orbit-slide'>Slide 1</li>\n"
                        "    <li class='orbit-slide'>Slide 2</li>\n"
                        "  </ul>\n"
                        "</div>"
                    ),
                    "react": (
                        "// BEFORE\n"
                        "<div className='carousel'>\n"
                        "  {slides.map(s => <div className='orbit-slide'>{s}</div>)}\n"
                        "</div>\n\n"
                        "// AFTER\n"
                        "<div className='carousel'>\n"
                        "  <ul>\n"
                        "    {slides.map(s => <li className='orbit-slide'>{s}</li>)}\n"
                        "  </ul>\n"
                        "</div>"
                    ),
                },
                "developer_tips": [
                    "Check if carousel library supports semantic HTML (most do)",
                    "Test that keyboard navigation still works after change",
                    "May need to adjust CSS if <ul> has default margins/padding",
                    "Add role='list' if CSS list-style:none removes semantics"
                ]
            }
        })

        if rid not in kb_map:
            return None
        entry = kb_map[rid]
        return {
            "rule_id": rid,
            "wcag_refs": entry.get("wcag_refs", []),
            "common_causes": entry.get("common_causes", []),
            "guidance": entry.get("guidance_by_framework", {}).get(framework, entry.get("guidance_by_framework", {}).get("html", "")),
            "example": entry.get("example_by_framework", {}).get(framework, entry.get("example_by_framework", {}).get("html", "")),
            "developer_tips": entry.get("developer_tips", [])
        }

    def _make_api_call(self, prompt: str) -> Optional[str]:
        """Make the actual API call to OpenRouter with rate limiting and retry logic"""
        
        # Apply rate limiting
        with self._rate_limiter:
            elapsed = time.time() - self._last_call_time
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
            
            try:
                # Build payload
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a web accessibility expert. You MUST respond with ONLY valid JSON, no markdown, no explanation text."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
                
                # Only add response_format for models that explicitly support it
                if self.supports_json_mode:
                    payload["response_format"] = {"type": "json_object"}
                
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self.timeout
                )
                
                # Update last call time after request completes
                self._last_call_time = time.time()

                if response.status_code == 200:
                    data = response.json()
                    try:
                        choices = data.get('choices') or []
                        if not choices:
                            logger.error("API response has no choices field")
                            with self._usage_lock:
                                self.usage_stats.add_failure()
                            return None
                        message = choices[0].get('message') or {}
                        content_raw = message.get('content')
                        # OpenRouter usually returns a string, but be permissive
                        if isinstance(content_raw, str):
                            content = content_raw
                        elif isinstance(content_raw, (dict, list)):
                            # Some providers return structured content; serialize for downstream parser
                            content = json.dumps(content_raw)
                        else:
                            logger.error(f"API response content missing or unexpected type: {type(content_raw)}")
                            logger.debug(f"Full message payload: {message}")
                            with self._usage_lock:
                                self.usage_stats.add_failure()
                            return None
                        
                        # Extract usage information from response
                        usage = data.get('usage', {})
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                        
                        # Calculate cost (will be 0 for free models)
                        cost = (
                            (prompt_tokens / 1_000_000 * self.price_per_1m_prompt_tokens) +
                            (completion_tokens / 1_000_000 * self.price_per_1m_completion_tokens)
                        )
                        
                        # Track usage
                        with self._usage_lock:
                            self.usage_stats.add_usage(prompt_tokens, completion_tokens, cost)
                        
                        logger.debug(
                            f"API call successful (took {response.elapsed.total_seconds():.2f}s, "
                            f"tokens: {prompt_tokens}+{completion_tokens}={prompt_tokens+completion_tokens}, "
                            f"cost: ${cost:.4f})"
                        )
                        return content
                    except Exception as e:
                        logger.error(f"Unexpected response format: {e}")
                        with self._usage_lock:
                            self.usage_stats.add_failure()
                        return None
                
                elif response.status_code == 429:
                    # Rate limit hit - the retry logic already handled retries
                    logger.warning(f"Rate limit exceeded even after retries: {response.text}")
                    with self._usage_lock:
                        self.usage_stats.add_failure()
                    return None
                
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    # Try to get error details
                    try:
                        error_data = response.json()
                        logger.error(f"API error details: {error_data}")
                    except Exception:
                        pass
                    with self._usage_lock:
                        self.usage_stats.add_failure()
                    return None

            except requests.exceptions.Timeout:
                logger.error(f"API request timed out after {self.timeout}s")
                with self._usage_lock:
                    self.usage_stats.add_failure()
                return None
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error - check internet connection: {e}")
                with self._usage_lock:
                    self.usage_stats.add_failure()
                return None
            except Exception as e:
                logger.error(f"API request failed: {e}")
                with self._usage_lock:
                    self.usage_stats.add_failure()
                return None

    def _extract_json_object(self, text: str) -> str:
        """Extract JSON object from text, handling markdown blocks and common issues"""
        text = text.strip()
        
        # Remove markdown code blocks
        text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n?```\s*', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        # Find JSON object boundaries
        start = text.find('{')
        end = text.rfind('}')
        
        if start == -1 or end == -1 or end < start:
            logger.warning("Could not find JSON object boundaries in response")
            return text
        
        # Extract just the JSON
        json_str = text[start:end + 1]
        
        # Fix common JSON syntax issues
        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        return json_str

    def _salvage_response(self, parsed_raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try to salvage a partially valid response"""
        try:
            # Ensure required fields have reasonable defaults
            salvaged = {
                "priority": parsed_raw.get("priority", "medium"),
                "user_impact": parsed_raw.get("user_impact", "May affect accessibility"),
                "fix_suggestion": parsed_raw.get("fix_suggestion", ["Review accessibility guidelines"]),
                "effort_minutes": parsed_raw.get("effort_minutes", 15),
                "effort_rationale": parsed_raw.get("effort_rationale"),
                "wcag_refs": parsed_raw.get("wcag_refs", []),
                "acceptance_criteria": parsed_raw.get("acceptance_criteria", []),
                "test_steps": parsed_raw.get("test_steps", []),
                "code_example": parsed_raw.get("code_example"),
                "fix_plan": parsed_raw.get("fix_plan", []),
                "__fallback__": False
            }
            
            # Validate the salvaged version
            AIResponse(**salvaged)
            logger.info("✓ Successfully salvaged partial response")
            return salvaged
            
        except Exception as e:
            logger.debug(f"Could not salvage response: {e}")
            return None

    def _validate_fix_suggestions(self, suggestions: List[str]) -> List[str]:
        """Validate and warn about fix suggestion quality without rejecting them."""
        WEAK_VERBS = ['review', 'ensure', 'consider', 'verify', 'check']
        ACTION_VERBS = ['add', 'remove', 'change', 'replace', 'update', 'wrap', 'move', 'set']

        validated: List[str] = []
        for suggestion in suggestions or []:
            try:
                lower = suggestion.lower()
            except Exception:
                validated.append(str(suggestion))
                continue

            first_word = suggestion.split()[0].lower() if suggestion.split() else ''
            if first_word in WEAK_VERBS and not any(verb in lower for verb in ACTION_VERBS):
                logger.warning(f"Vague fix suggestion detected: {suggestion[:120]}")

            has_selector = any(ch in suggestion for ch in ['.', '#', '[', '<'])
            has_specifics = any(ch in suggestion for ch in [':', '=', '"', "'"])

            if not (has_selector or has_specifics) and len(suggestion) > 50:
                logger.warning(f"Fix suggestion lacks specifics: {suggestion[:120]}")

            validated.append(suggestion)

        return validated

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response with enhanced error handling for Mistral"""
        try:
            # Debug logging
            logger.debug("RAW AI RESPONSE (first 1000 chars):\n%s", response_text[:1000])
            
            # Extract and clean JSON
            json_str = self._extract_json_object(response_text)
            json_str = _clean_json_text(json_str)
            
            logger.debug("CLEANED JSON (first 500 chars):\n%s", json_str[:500])
            
            # Try to parse JSON
            try:
                parsed_raw = json.loads(json_str, strict=False)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed at line {e.lineno}, col {e.colno}: {e.msg}")
                logger.debug(f"Failed text around error:\n{json_str[max(0, e.pos-100):e.pos+100]}")
                
                # Try one more time with even more aggressive cleaning
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)  # Remove control chars
                parsed_raw = json.loads(json_str, strict=False)

            # Validate using strict Pydantic model
            try:
                validated = AIResponse(**parsed_raw)
                # Check fix suggestion quality and warn as needed
                try:
                    self._validate_fix_suggestions(validated.fix_suggestion)
                except Exception:
                    logger.debug("Failed to validate fix suggestions quality")
            except ValidationError as ve:
                logger.warning(f"Pydantic validation failed: {ve.errors()}")
                logger.debug(f"Raw parsed data: {parsed_raw}")
                
                # Try to salvage what we can
                salvaged = self._salvage_response(parsed_raw)
                if salvaged:
                    return salvaged
                
                # Fall back to default
                fb = self._get_fallback_response()
                fb["__fallback__"] = True
                return fb

            # Clamp effort_minutes to a reasonable range
            if validated.effort_minutes < 1 or validated.effort_minutes > 240:
                validated.effort_minutes = 15

            result = validated.dict()
            result["__fallback__"] = False
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response (first 500 chars): {response_text[:500]}")
            fb = self._get_fallback_response()
            fb["__fallback__"] = True
            return fb
        except Exception as e:
            logger.error(f"Unexpected error parsing AI response: {e}")
            logger.debug(f"Raw response (first 500 chars): {response_text[:500]}")
            fb = self._get_fallback_response()
            fb["__fallback__"] = True
            return fb

    def _get_fallback_response(self) -> Dict[str, Any]:
        """Provide a sensible fallback when AI fails"""
        return {
            "priority": "medium",
            "user_impact": "This accessibility issue may affect users with disabilities.",
            "fix_suggestion": ["Review and fix the accessibility issue following WCAG guidelines."],
            "code_example": None,
            "effort_minutes": 15
        }

    def test_connection(self) -> bool:
        """Test if the AI API is reachable and working"""
        if not self.is_available():
            return False

        try:
            # Simple test prompt
            test_prompt = "Respond with JSON: {\"status\": \"ok\", \"message\": \"test successful\"}"
            response = self._make_api_call(test_prompt)
            return response is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def test_model_json_capability(self) -> Dict[str, Any]:
        """Test if the current model can produce valid JSON reliably"""
        if not self.is_available():
            return {"error": "API key not available"}
        
        test_prompt = (
            "Respond with ONLY this JSON object, no other text:\n"
            '{"test": "success", "number": 42, "array": ["a", "b"], "nested": {"key": "value"}}'
        )
        
        try:
            response = self._make_api_call(test_prompt)
            if not response:
                return {"error": "No response from API", "model": self.model}
            
            # Try to parse
            try:
                parsed = json.loads(response)
                return {
                    "success": True,
                    "model": self.model,
                    "response": parsed,
                    "raw_length": len(response),
                    "message": "✓ Model can produce valid JSON"
                }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "model": self.model,
                    "error": str(e),
                    "raw_response": response[:500],
                    "message": "✗ Model produced invalid JSON"
                }
        except Exception as e:
            return {"error": f"Test failed: {e}", "model": self.model}

    # =====================================================
    # ASYNC API METHODS (for batch processing)
    # =====================================================
    
    async def _make_api_call_async(self, prompt: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Async version of API call for batch processing"""
        
        try:
            # Build payload (same as sync version)
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a web accessibility expert. You MUST respond with ONLY valid JSON, no markdown, no explanation text."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }
            
            # Only add response_format for models that support it
            if self.supports_json_mode:
                payload["response_format"] = {"type": "json_object"}
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    try:
                        choices = data.get('choices') or []
                        if not choices:
                            logger.error("API response has no choices field")
                            with self._usage_lock:
                                self.usage_stats.add_failure()
                            return None
                        message = choices[0].get('message') or {}
                        content = message.get('content')
                        if not isinstance(content, str):
                            logger.error("API response content missing or not a string")
                            with self._usage_lock:
                                self.usage_stats.add_failure()
                            return None
                        
                        # Extract usage information
                        usage = data.get('usage', {})
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                        
                        # Calculate cost
                        cost = (
                            (prompt_tokens / 1_000_000 * self.price_per_1m_prompt_tokens) +
                            (completion_tokens / 1_000_000 * self.price_per_1m_completion_tokens)
                        )
                        
                        # Track usage
                        with self._usage_lock:
                            self.usage_stats.add_usage(prompt_tokens, completion_tokens, cost)
                        
                        logger.debug(
                            f"Async API call successful "
                            f"(tokens: {prompt_tokens}+{completion_tokens}={prompt_tokens+completion_tokens}, "
                            f"cost: ${cost:.4f})"
                        )
                        return content
                    except Exception as e:
                        logger.error(f"Unexpected response format: {e}")
                        with self._usage_lock:
                            self.usage_stats.add_failure()
                        return None
                
                elif response.status == 429:
                    logger.warning(f"Rate limit exceeded: {await response.text()}")
                    with self._usage_lock:
                        self.usage_stats.add_failure()
                    return None
                
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    with self._usage_lock:
                        self.usage_stats.add_failure()
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Async API request timed out after {self.timeout}s")
            with self._usage_lock:
                self.usage_stats.add_failure()
            return None
        except Exception as e:
            logger.error(f"Async API request failed: {e}")
            with self._usage_lock:
                self.usage_stats.add_failure()
            return None

    async def analyze_accessibility_issue_async(
        self, 
        issue_description: str, 
        elements: Optional[list] = None, 
        impact: Optional[str] = None, 
        rule_id: Optional[str] = None, 
        framework: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Async version of analyze_accessibility_issue for batch processing
        
        Args:
            session: Optional aiohttp session (will create one if not provided)
        """
        if not self.is_available():
            return None

        # Build the prompt (same as sync version). Infer element_count if possible.
        element_count = None
        if elements and isinstance(elements, list):
            element_count = len(elements)
        prompt = self._build_comprehensive_prompt(issue_description, elements, impact, rule_id, framework, element_count)
        
        # Use provided session or create a new one
        if session:
            response_text = await self._make_api_call_async(prompt, session)
        else:
            async with aiohttp.ClientSession() as new_session:
                response_text = await self._make_api_call_async(prompt, new_session)
        
        if not response_text:
            return None

        return self._parse_ai_response(response_text)
    
    async def analyze_batch_async(
        self,
        issues: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Analyze multiple accessibility issues in parallel with controlled concurrency
        
        Args:
            issues: List of issue dicts with keys: description, elements, impact, rule_id, framework
            max_concurrent: Maximum number of concurrent API calls (default: 5)
        
        Returns:
            List of analysis results (same order as input)
        
        Example:
            issues = [
                {"description": "Missing alt text", "rule_id": "image-alt"},
                {"description": "Low contrast", "rule_id": "color-contrast"},
            ]
            results = await client.analyze_batch_async(issues, max_concurrent=3)
        """
        if not self.is_available():
            return [None] * len(issues)
        
        if not issues:
            return []
        
        logger.info(f"Starting async batch analysis of {len(issues)} issues (max {max_concurrent} concurrent)")
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(issue: Dict[str, Any], session: aiohttp.ClientSession):
            """Wrapper to control concurrency"""
            async with semaphore:
                return await self.analyze_accessibility_issue_async(
                    issue_description=issue.get("description", ""),
                    elements=issue.get("elements"),
                    impact=issue.get("impact"),
                    rule_id=issue.get("rule_id"),
                    framework=issue.get("framework"),
                    session=session
                )
        
        # Process all issues in parallel with rate limiting via semaphore
        async with aiohttp.ClientSession() as session:
            tasks = [analyze_with_semaphore(issue, session) for issue in issues]
            results = await asyncio.gather(*tasks, return_exceptions=False)
        
        logger.info(f"Batch analysis complete. Successful: {sum(1 for r in results if r is not None)}/{len(issues)}")
        logger.info(f"Current usage stats: {self.get_usage_stats()}")
        
        return results

    def close(self) -> None:
        """
        Clean up underlying HTTP resources.

        Safe to call multiple times.
        """
        try:
            if hasattr(self, "session") and self.session is not None:
                self.session.close()
        except Exception as exc:
            logger.debug("Error while closing HTTP session: %s", exc)

    def __enter__(self) -> "SimpleAIClient":
        """
        Allow usage as a context manager:

            with SimpleAIClient() as client:
                ...

        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
