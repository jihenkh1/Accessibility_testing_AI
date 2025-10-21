import os
import requests
import json
import logging
import time
import asyncio
import aiohttp
from threading import Lock
from typing import Dict, Any, Optional, List, Literal
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ValidationError

try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    load_dotenv(find_dotenv(usecwd=True), override=False)
except Exception:
    # Safe fallback when python-dotenv is not installed
    pass

logger = logging.getLogger(__name__)

# Version tag for prompt templates; bump when changing prompt shape materially
PROMPT_VERSION = "v1"


def _get_cfg(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Resolve configuration from environment variables only.
    
    ⚠️ SECURITY: Does NOT cache sensitive values like API keys.
    Always reads fresh from environment to avoid secrets in memory.
    
    Order: environment variable -> default
    - .env is already loaded via python-dotenv at import time (if installed)
    
    Args:
        name: Configuration variable name (e.g., 'OPENROUTER_API_KEY')
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    val = os.getenv(name)
    if val is not None and val != "":
        return val
    return default


class AIResponse(BaseModel):
    """Strict schema for AI enrichment output."""
    priority: Literal['critical', 'high', 'medium', 'low'] = Field(default='medium')
    user_impact: str = ""
    fix_suggestion: str = ""
    effort_minutes: int = 15

    # Optional, richer fields for future UI enhancements
    code_example: Optional[str] = None
    wcag_refs: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    test_steps: List[str] = Field(default_factory=list)
    automation_hints: List[str] = Field(default_factory=list)
    personas_impact: Optional[Dict[str, str]] = None
    root_cause_hypothesis: Optional[str] = None
    component_guess: Optional[str] = None
    fix_plan: Optional[Dict[str, List[str]]] = None
    ticket_title: Optional[str] = None
    ticket_body: Optional[str] = None
    confidence: Optional[int] = None
    risk_level: Optional[str] = None


@dataclass
class UsageStats:
    """Track token usage and cost metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int, cost: float = 0.0):
        """Add usage from a single API call"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += (prompt_tokens + completion_tokens)
        self.estimated_cost_usd += cost
    
    def add_failure(self):
        """Record a failed request"""
        self.total_requests += 1
        self.failed_requests += 1
    
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
    """

    def __init__(self):
        self.api_key = _get_cfg('OPENROUTER_API_KEY')
        self.base_url = _get_cfg('OPENROUTER_BASE_URL', "https://openrouter.ai/api/v1")
        self.model = _get_cfg('OPENROUTER_MODEL', "tngtech/deepseek-r1t2-chimera:free")  # Default model
        try:
            self.timeout = int(_get_cfg('OPENROUTER_TIMEOUT', "30") or "30")
        except ValueError:
            self.timeout = 30

        # Rate limiting setup
        self._rate_limiter = Lock()
        self._last_call_time = 0.0
        self._min_interval = 0.2  # 200ms between calls = max 5 requests/second
        
        # Usage tracking
        self.usage_stats = UsageStats()
        
        # Pricing per 1M tokens (update these based on your model)
        # For free models, these will be 0
        self.price_per_1m_prompt_tokens = 0.0
        self.price_per_1m_completion_tokens = 0.0
        
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

        if not self.api_key:
            logger.warning("OpenRouter API key not found. AI features will be disabled.")
        else:
            logger.info("AI Client initialized with OpenRouter (rate limiting + usage tracking enabled)")

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
        self.usage_stats = UsageStats()
        logger.info("Usage statistics reset")

    def analyze_accessibility_issue(self, issue_description: str, elements: Optional[list] = None, impact: Optional[str] = None, rule_id: Optional[str] = None, framework: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Comprehensive AI analysis for accessibility issues
        Returns: priority, user_impact, fix_suggestion, code_example, effort_minutes
        """
        if not self.is_available():
            return None
            
        prompt = self._build_comprehensive_prompt(issue_description, elements, impact, rule_id, framework)

        try:
            response = self._make_api_call(prompt)
            if response:
                return self._parse_ai_response(response)
            return None

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None

    def _build_comprehensive_prompt(self, issue_description: str, elements: Optional[list] = None, impact: Optional[str] = None, rule_id: Optional[str] = None, framework: Optional[str] = None) -> str:
        """Build comprehensive prompt using a compact knowledge base and structured requirements"""
        # Normalize inputs
        framework_norm = (framework or "html").lower()
        elems = list(elements or [])
        elems = elems[:3]  # keep prompt compact
        elements_text = f"Affected selectors: {elems}" if elems else "Affected selectors: []"
        impact_text = f"Impact level: {impact}" if impact else "Impact level: unknown"

        # Inject compact knowledge for common rule ids
        # Built-in compact knowledge base only (dynamic refs disabled)
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

        # Few-shot style: a single compact example to calibrate output (not a strict template)
        example_json = {
            "priority": "high",
            "user_impact": "Screen reader and keyboard users cannot identify the control.",
            "fix_suggestion": "Provide an accessible name via visible text or aria-label matching intent.",
            "effort_minutes": 15,
            "wcag_refs": ["WCAG 4.1.2"],
            "acceptance_criteria": [
                "Button announces a meaningful name to screen readers.",
                "Visible label or aria-label reflects the control purpose."
            ],
            "test_steps": [
                "Navigate to the control using Tab.",
                "Verify screen reader announces a descriptive name."
            ]
        }

        prompt = (
            "You are an expert web accessibility consultant. Analyze this issue and return strict JSON.\n\n"
            f"ISSUE: {issue_description}\n{elements_text}\n{impact_text}\n\n"
            f"Knowledge (use if relevant):\n{kb_text}\n"
            "Output JSON with these fields (use sensible defaults when unknown):\n"
            "- priority: critical|high|medium|low\n"
            "- user_impact: short explanation for real users\n"
            "- fix_suggestion: specific action for the given framework\n"
            "- effort_minutes: integer estimate (5-240)\n"
            "- wcag_refs: list of WCAG references (e.g., WCAG 1.1.1)\n"
            "- acceptance_criteria: list of concrete, testable criteria\n"
            "- test_steps: list of succinct steps for manual testing\n"
            "- code_example: optional short code snippet if helpful\n"
            "- component_guess, root_cause_hypothesis: optional\n\n"
            f"Example (for style only, do not copy literally): {json.dumps(example_json)}\n\n"
            f"Prompt-Version: {PROMPT_VERSION}\n"
            "Respond with ONLY valid JSON, no other text."
        )
        return prompt

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
                    "react": "On <img>, set alt. For background/decorative, ensure it’s ignored by AT.",
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
                    "react": "Use <label htmlFor=...> and input id; don’t rely on placeholder.",
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
            # Link purpose must be clear
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
            # Focus must be visible for keyboard users
            "focus-visible": {
                "wcag_refs": ["WCAG 2.4.7"],
                "common_causes": ["Outline removed via CSS", "Custom components without visible focus styles"],
                "guidance_by_framework": {
                    "html": "Ensure a visible focus indicator (:focus or :focus-visible); don’t remove outlines.",
                    "react": "Provide focus styles for interactive components; use :focus-visible or focus ring utilities.",
                },
                "example_by_framework": {
                    "html": "button:focus-visible{outline:2px solid #2563EB; outline-offset:2px;}",
                    "react": "<button className=\"focus:outline-blue-600 focus:outline-2\">Save</button>",
                },
            },
            # Headings: order and presence
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
            # Landmarks/regions
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
        if rid not in kb_map:
            return None
        entry = kb_map[rid]
        return {
            "rule_id": rid,
            "wcag_refs": entry.get("wcag_refs", []),
            "common_causes": entry.get("common_causes", []),
            "guidance": entry.get("guidance_by_framework", {}).get(framework, entry.get("guidance_by_framework", {}).get("html", "")),
            "example": entry.get("example_by_framework", {}).get(framework, entry.get("example_by_framework", {}).get("html", "")),
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
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a web accessibility expert. Always respond with valid JSON."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 800,  # Increased for code examples
                        "temperature": 0.1,  # Lower for more consistent JSON
                        "response_format": {"type": "json_object"}  # Force JSON mode if supported
                    },
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
                            self.usage_stats.add_failure()
                            return None
                        message = choices[0].get('message') or {}
                        content = message.get('content')
                        if not isinstance(content, str):
                            logger.error("API response content missing or not a string")
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
                        self.usage_stats.add_usage(prompt_tokens, completion_tokens, cost)
                        
                        logger.debug(
                            f"API call successful (took {response.elapsed.total_seconds():.2f}s, "
                            f"tokens: {prompt_tokens}+{completion_tokens}={prompt_tokens+completion_tokens}, "
                            f"cost: ${cost:.4f})"
                        )
                        return content
                    except Exception as e:
                        logger.error(f"Unexpected response format: {e}")
                        self.usage_stats.add_failure()
                        return None
                
                elif response.status_code == 429:
                    # Rate limit hit - the retry logic already handled retries
                    logger.warning(f"Rate limit exceeded even after retries: {response.text}")
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
                    self.usage_stats.add_failure()
                    return None

            except requests.exceptions.Timeout:
                logger.error(f"API request timed out after {self.timeout}s")
                self.usage_stats.add_failure()
                return None
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error - check internet connection: {e}")
                self.usage_stats.add_failure()
                return None
            except Exception as e:
                logger.error(f"API request failed: {e}")
                self.usage_stats.add_failure()
                return None

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response with better error handling and fallbacks"""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()

            # Remove markdown code blocks if present
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]  # Remove ```
            
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove ```
            
            cleaned_text = cleaned_text.strip()

            # Try to parse JSON
            try:
                parsed_raw = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                # Try to fix common JSON issues
                logger.debug(f"Initial JSON parse failed: {e}, attempting cleanup...")
                
                # Try to extract JSON object if there's extra text
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    cleaned_text = cleaned_text[start_idx:end_idx + 1]
                    parsed_raw = json.loads(cleaned_text)
                else:
                    raise  # Re-raise if we can't fix it

            # Validate using strict Pydantic model
            try:
                validated = AIResponse(**parsed_raw)
            except ValidationError as ve:
                logger.warning(f"AI response validation failed, using fallback: {ve.errors()}")
                return self._get_fallback_response()

            # Clamp effort_minutes to a reasonable range
            if validated.effort_minutes < 1 or validated.effort_minutes > 240:
                validated.effort_minutes = 15

            return validated.dict()

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response (first 500 chars): {response_text[:500]}")
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f"Unexpected error parsing AI response: {e}")
            return self._get_fallback_response()

    def _get_fallback_response(self) -> Dict[str, Any]:
        """Provide a sensible fallback when AI fails"""
        return {
            "priority": "medium",
            "user_impact": "This accessibility issue may affect users with disabilities.",
            "fix_suggestion": "Review and fix the accessibility issue following WCAG guidelines.",
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

    # =====================================================
    # ASYNC API METHODS (for batch processing)
    # =====================================================
    
    async def _make_api_call_async(self, prompt: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Async version of API call for batch processing"""
        
        # Note: Rate limiting is handled at the batch level, not per call
        # in the async version to allow parallel execution
        
        try:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a web accessibility expert. Always respond with valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 800,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    try:
                        choices = data.get('choices') or []
                        if not choices:
                            logger.error("API response has no choices field")
                            self.usage_stats.add_failure()
                            return None
                        message = choices[0].get('message') or {}
                        content = message.get('content')
                        if not isinstance(content, str):
                            logger.error("API response content missing or not a string")
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
                        self.usage_stats.add_usage(prompt_tokens, completion_tokens, cost)
                        
                        logger.debug(
                            f"Async API call successful "
                            f"(tokens: {prompt_tokens}+{completion_tokens}={prompt_tokens+completion_tokens}, "
                            f"cost: ${cost:.4f})"
                        )
                        return content
                    except Exception as e:
                        logger.error(f"Unexpected response format: {e}")
                        self.usage_stats.add_failure()
                        return None
                
                elif response.status == 429:
                    logger.warning(f"Rate limit exceeded: {await response.text()}")
                    self.usage_stats.add_failure()
                    return None
                
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    self.usage_stats.add_failure()
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Async API request timed out after {self.timeout}s")
            self.usage_stats.add_failure()
            return None
        except Exception as e:
            logger.error(f"Async API request failed: {e}")
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

        # Build the prompt (same as sync version)
        prompt = self._build_comprehensive_prompt(issue_description, elements, impact, rule_id, framework)
        
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

