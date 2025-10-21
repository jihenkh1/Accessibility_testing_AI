"""
Pa11y-based accessibility scanner that runs locally without AI API costs.

This module uses Pa11y (Node.js tool) to scan websites for accessibility issues.
Pa11y can use multiple runners (axe-core, HTML CodeSniffer) and runs locally,
eliminating API rate limits and costs.

Installation required:
    npm install -g pa11y pa11y-ci
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

# Fix for Windows async issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


async def scan_url_with_pa11y(
    url: str,
    runner: str = "axe",  # 'axe' or 'htmlcs'
    standard: str = "WCAG2AA",  # WCAG2A, WCAG2AA, WCAG2AAA
    timeout: int = 30000,
    wait: int = 1000,
) -> Dict[str, Any]:
    """
    Scan a single URL using Pa11y.
    
    Args:
        url: The URL to scan
        runner: Which engine to use ('axe' or 'htmlcs')
        standard: WCAG standard to test against
        timeout: Page load timeout in ms
        wait: Time to wait after page load in ms
    
    Returns:
        Dict with Pa11y results in format:
        {
            "issues": [...],
            "pageUrl": "...",
            "documentTitle": "..."
        }
    """
    try:
        # Build Pa11y command
        cmd = [
            "pa11y",
            "--reporter", "json",
            "--runner", runner,
            "--standard", standard,
            "--timeout", str(timeout),
            "--wait", str(wait),
            url
        ]
        
        # Run Pa11y
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0 or result.returncode == 2:  # 2 means issues found
            try:
                data = json.loads(stdout.decode())
                return {
                    "issues": data if isinstance(data, list) else data.get("issues", []),
                    "pageUrl": url,
                    "documentTitle": ""
                }
            except json.JSONDecodeError:
                return {"issues": [], "pageUrl": url, "documentTitle": ""}
        else:
            # Pa11y failed
            error_msg = stderr.decode() if stderr else "Unknown error"
            print(f"Pa11y scan failed for {url}: {error_msg}")
            return {"issues": [], "pageUrl": url, "documentTitle": ""}
            
    except FileNotFoundError:
        print("❌ Pa11y not found. Install with: npm install -g pa11y")
        return {"issues": [], "pageUrl": url, "documentTitle": ""}
    except Exception as e:
        print(f"Error scanning {url} with Pa11y: {e}")
        return {"issues": [], "pageUrl": url, "documentTitle": ""}


async def scan_sitemap_with_pa11y(
    urls: List[str],
    runner: str = "axe",
    standard: str = "WCAG2AA",
    max_concurrent: int = 3,
) -> Dict[str, Any]:
    """
    Scan multiple URLs using Pa11y with concurrency control.
    
    Args:
        urls: List of URLs to scan
        runner: Which engine to use ('axe' or 'htmlcs')
        standard: WCAG standard to test against
        max_concurrent: Maximum concurrent scans
    
    Returns:
        Aggregated results from all pages
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def scan_with_semaphore(url: str):
        async with semaphore:
            return await scan_url_with_pa11y(url, runner, standard)
    
    # Scan all URLs concurrently (with limit)
    results = await asyncio.gather(*[scan_with_semaphore(url) for url in urls])
    
    # Aggregate issues
    all_issues = []
    for result in results:
        all_issues.extend(result.get("issues", []))
    
    return {
        "issues": all_issues,
        "pageUrl": urls[0] if urls else "",
        "documentTitle": "",
        "scannedPages": len(urls),
        "totalIssues": len(all_issues)
    }


def check_pa11y_installed() -> bool:
    """Check if Pa11y is installed and available."""
    try:
        result = subprocess.run(
            ["pa11y", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_installation_instructions() -> str:
    """Get platform-specific installation instructions for Pa11y."""
    return """
Pa11y is not installed. To install:

1. Install Node.js (if not already installed):
   - Windows: Download from https://nodejs.org/
   - Mac: brew install node
   - Linux: sudo apt-get install nodejs npm

2. Install Pa11y globally:
   npm install -g pa11y

3. Verify installation:
   pa11y --version

Optional: Install Pa11y CI for scanning multiple URLs:
   npm install -g pa11y-ci
"""


# Synchronous wrapper for easier integration
def scan_url_sync(url: str, runner: str = "axe") -> Dict[str, Any]:
    """Synchronous wrapper for scan_url_with_pa11y."""
    return asyncio.run(scan_url_with_pa11y(url, runner=runner))


def scan_multiple_urls_sync(urls: List[str], runner: str = "axe") -> Dict[str, Any]:
    """Synchronous wrapper for scan_sitemap_with_pa11y."""
    return asyncio.run(scan_sitemap_with_pa11y(urls, runner=runner))
