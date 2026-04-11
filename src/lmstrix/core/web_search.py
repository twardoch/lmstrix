# this_file: src/lmstrix/core/web_search.py
"""Web search via Poe API: search for model info and fetch page content."""

from __future__ import annotations

import os
import re
from html.parser import HTMLParser

import httpx
from loguru import logger

# Poe search model mapping: search_code -> (poe_model_name, description)
SEARCH_MODELS: dict[int, tuple[str, str]] = {
    1: ("Web-Search", "web-search"),
    2: ("Duck-Duck-Search", "ddg-search"),
}

MAX_URLS_TO_FETCH = 5
MAX_PAGE_CHARS = 3000
FETCH_TIMEOUT_SECS = 15
MAX_TOTAL_CONTENT_CHARS = 12000


class _HTMLTextExtractor(HTMLParser):
    """Extract visible text from HTML, skipping script/style tags."""

    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: ARG002
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._pieces.append(data)

    def get_text(self) -> str:
        return " ".join(self._pieces)


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text using stdlib parser."""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
    except Exception:
        parser = _HTMLTextExtractor()
        try:
            parser.feed(html)
            text = parser.get_text()
        except Exception:
            text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


def poe_search(query: str, search_code: int) -> str | None:
    """Call Poe API to perform a web search. Returns raw response text."""
    api_key = os.getenv("POE_API_KEY")
    if not api_key:
        logger.error("POE_API_KEY environment variable not set. Cannot perform web search.")
        return None

    model_info = SEARCH_MODELS.get(search_code)
    if not model_info:
        logger.error(f"Invalid search code {search_code}. Use 1 (web-search) or 2 (ddg-search).")
        return None

    poe_model, label = model_info
    logger.debug(f"Searching via Poe ({label}): {query}")

    try:
        import openai

        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.poe.com/v1",
        )
        response = client.chat.completions.create(
            model=poe_model,
            messages=[{"role": "user", "content": query}],
        )
        content = response.choices[0].message.content
        logger.debug(f"Search returned {len(content or '')} chars")
        return content
    except Exception as e:
        logger.error(f"Poe search failed: {e}")
        return None


def parse_search_urls(search_text: str) -> list[str]:
    """Extract URLs from Poe search result text.

    Expects format like:
        1. **Title**
           Description
           🔗 https://example.com/page
    """
    urls = re.findall(r"🔗\s*(https?://\S+)", search_text)
    if not urls:
        # Fallback: find any URLs in the text
        urls = re.findall(r"https?://[^\s\)\"'>]+", search_text)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique[:MAX_URLS_TO_FETCH]


def fetch_page_text(url: str) -> str | None:
    """Fetch a web page and extract its text content, truncated to MAX_PAGE_CHARS."""
    logger.debug(f"Fetching {url}")
    try:
        with httpx.Client(timeout=FETCH_TIMEOUT_SECS, follow_redirects=True) as client:
            resp = client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; lmstrix/1.0)"},
            )
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                logger.debug(f"Skipping non-text content: {content_type}")
                return None
            text = _html_to_text(resp.text)
            if len(text) > MAX_PAGE_CHARS:
                text = text[:MAX_PAGE_CHARS] + "..."
            return text
    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None


def search_model_info(model_id: str, search_code: int) -> str | None:
    """Search for model info and fetch page content. Returns combined text or None.

    Args:
        model_id: The model identifier to search for.
        search_code: 1 for web-search, 2 for ddg-search.
    """
    if search_code not in SEARCH_MODELS:
        return None

    query = f"{model_id} model"
    search_text = poe_search(query, search_code)
    if not search_text:
        return None

    urls = parse_search_urls(search_text)
    if not urls:
        logger.warning(f"No URLs found in search results for {model_id}")
        # Still return search snippets as context
        return f"Search results for '{model_id}':\n{search_text[:MAX_TOTAL_CONTENT_CHARS]}"

    logger.info(f"Fetching content from {len(urls)} URLs for {model_id}")

    parts: list[str] = []
    total_chars = 0
    for url in urls:
        if total_chars >= MAX_TOTAL_CONTENT_CHARS:
            break
        text = fetch_page_text(url)
        if text and len(text) > 100:  # Skip very short pages
            remaining = MAX_TOTAL_CONTENT_CHARS - total_chars
            if len(text) > remaining:
                text = text[:remaining] + "..."
            parts.append(f"--- Content from {url} ---\n{text}")
            total_chars += len(text)

    if not parts:
        # Fall back to search snippets
        return f"Search results for '{model_id}':\n{search_text[:MAX_TOTAL_CONTENT_CHARS]}"

    return "\n\n".join(parts)
