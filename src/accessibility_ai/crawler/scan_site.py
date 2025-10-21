import asyncio
import sys
from urllib.parse import urlparse, urljoin
from typing import Set, Deque, Dict, Any, List, Tuple
from collections import deque

# Fix for Windows Playwright async issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js"


async def _scan_page(page, url: str) -> Dict[str, Any]:
    """Inject axe-core and run a11y checks on a single page.

    Returns an axe-like result dict with `violations`.
    """
    try:
        # Ensure page is loaded
        await page.goto(url, wait_until="domcontentloaded")
        # Inject axe-core
        await page.add_script_tag(url=AXE_CDN)
        # Wait for axe to be available
        await page.wait_for_function("() => window.axe !== undefined", timeout=10000)
        results = await page.evaluate("""
            async () => {
                const res = await window.axe.run(document, { resultTypes: ['violations'] });
                return res;
            }
        """)
        return results or {"violations": []}
    except Exception:
        return {"violations": []}


def _normalize_url(u: str) -> str:
    return u.split('#')[0].rstrip('/')


async def _crawl(start_url: str, max_pages: int = 20, same_origin_only: bool = True) -> Dict[str, Any]:
    from playwright.async_api import async_playwright

    parsed_origin = urlparse(start_url)
    origin_host = parsed_origin.netloc
    origin_scheme = parsed_origin.scheme

    visited: Set[str] = set()
    q: Deque[str] = deque([start_url])
    aggregated: Dict[str, Any] = {"violations": []}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            while q and len(visited) < max_pages:
                url = q.popleft()
                url = _normalize_url(url)
                if url in visited:
                    continue
                visited.add(url)

                res = await _scan_page(page, url)
                # Merge violations; carry page context by prefixing selectors with the URL
                for v in res.get("violations", []):
                    v_copy = {
                        "id": v.get("id", "unknown"),
                        "description": v.get("description", ""),
                        "impact": v.get("impact", "moderate"),
                        "nodes": [],
                    }
                    for node in v.get("nodes", []):
                        targets = node.get("target", [])
                        if isinstance(targets, list):
                            prefixed = [f"{url} :: {str(t)}" for t in targets]
                        else:
                            prefixed = [f"{url} :: {str(targets)}"]
                        v_copy["nodes"].append({"target": prefixed})
                    aggregated["violations"].append(v_copy)

                # Extract links
                try:
                    hrefs: List[str] = await page.eval_on_selector_all(
                        "a[href]",
                        "els => els.map(e => e.getAttribute('href')).filter(Boolean)",
                    )
                except Exception:
                    hrefs = []

                # Enqueue normalized, same-origin links
                for href in hrefs:
                    abs_url = urljoin(url + '/', href)
                    parsed = urlparse(abs_url)
                    if same_origin_only and (parsed.scheme != origin_scheme or parsed.netloc != origin_host):
                        continue
                    norm = _normalize_url(abs_url)
                    if norm not in visited:
                        q.append(norm)
        finally:
            await context.close()
            await browser.close()

    return aggregated


def scan_site(start_url: str, max_pages: int = 20, same_origin_only: bool = True) -> Dict[str, Any]:
    """Public API: crawl pages and return an aggregated axe-like report."""
    return asyncio.run(_crawl(start_url, max_pages=max_pages, same_origin_only=same_origin_only))

