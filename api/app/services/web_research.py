"""Lightweight web research for the drafting feature's template-format lookup: plain
HTTP fetch + HTML parsing, no browser. Verified during build against real legal-
drafting-format queries - DuckDuckGo's HTML endpoint returns usable results without an
API key (Google blocks/CAPTCHAs non-API automated requests, which is why this targets
DuckDuckGo specifically, not because of any preference beyond "it actually works").

This never fabricates having found something: if search or every fetch fails, the
caller (agents_sdk/template_research_agent.py) is told there's no source material and
falls back to a labeled "standard structure, not sourced" result rather than pretending
to have researched anything.
"""
import logging
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("second_brain.web_research")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
_SEARCH_URL = "https://html.duckduckgo.com/html/"
_MAX_PAGE_CHARS = 6000


def _resolve_ddg_redirect(href: str) -> str | None:
    """DuckDuckGo's HTML results wrap the real URL in a redirect link
    (//duckduckgo.com/l/?uddg=<url-encoded target>&...) - unwrap it."""
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg")
        return target[0] if target else None
    return href


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Returns [{title, url}, ...]. Empty list on any failure - callers must treat
    that as "no source material," never retry-until-success (a demo can't depend on a
    third-party search endpoint always being reachable)."""
    try:
        response = httpx.get(_SEARCH_URL, params={"q": query}, headers=_HEADERS, timeout=10, follow_redirects=True)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("web search failed for %r: %s", query, exc)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for link in soup.select("a.result__a")[:max_results]:
        url = _resolve_ddg_redirect(link.get("href", ""))
        title = link.get_text(strip=True)
        if url and title:
            results.append({"title": title, "url": url})
    return results


def fetch_page_text(url: str, max_chars: int = _MAX_PAGE_CHARS) -> str | None:
    """Fetches a page and returns its visible text, truncated. None if the page isn't
    fetchable HTML (PDFs and other binary formats are skipped, not parsed as text)."""
    try:
        response = httpx.get(url, headers=_HEADERS, timeout=10, follow_redirects=True)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("failed to fetch %s: %s", url, exc)
        return None

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        logger.info("skipping non-HTML content at %s (content-type: %s)", url, content_type)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text[:max_chars] if text else None


def research_sources(query: str, max_pages: int = 3) -> list[dict]:
    """Search, then fetch the first `max_pages` results that actually yield usable
    text. Returns [{title, url, text}, ...] - possibly empty."""
    results = search_web(query, max_results=max_pages * 2)  # fetch some slack for skipped/failed pages
    sources = []
    for r in results:
        text = fetch_page_text(r["url"])
        if text:
            sources.append({"title": r["title"], "url": r["url"], "text": text})
        if len(sources) >= max_pages:
            break
    return sources
