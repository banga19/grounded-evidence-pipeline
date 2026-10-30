"""Turn a SearchResult into an Evidence record, capturing provenance.

For demo corpus URLs no network call is made - the snippet IS the content.
For live web results the page is fetched and stripped to text (stdlib
HTML parser, no scraping frameworks). A single bad page must never kill a
run: failures are recorded in the provenance dict and we fall back to the
search snippet.
"""

import html.parser
import logging

from ..search.base import SearchResult
from .models import Evidence, utcnow

logger = logging.getLogger(__name__)

DEMO_URL_PREFIX = "https://corpus.example.com/"


class _TextExtractor(html.parser.HTMLParser):
    """Minimal HTML-to-text extraction (stdlib only)."""

    SKIP_TAGS = {"script", "style", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks: list = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0 and data.strip():
            self.chunks.append(data.strip())


def strip_html(raw: str) -> str:
    """Strip tags/scripts/styles and collapse whitespace."""
    parser = _TextExtractor()
    parser.feed(raw)
    return " ".join(parser.chunks)


def _fetch(url: str, timeout: int = 8) -> str:
    import requests  # lazy import: offline demo mode never needs it

    resp = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "grounded-evidence-pipeline/0.1 (research prototype)"},
    )
    resp.raise_for_status()
    return strip_html(resp.text)


def fetch_and_extract(result: SearchResult, query_id: str, query_text: str) -> Evidence:
    """Fetch (or simulate) content for one search result and wrap it in Evidence."""
    is_demo = result.url.startswith(DEMO_URL_PREFIX)
    provenance = {
        "provider": result.provider,
        "provider_rank": result.rank,
        "retrieval_query": query_text,
        "retrieved_at": utcnow(),
        "extraction_method": "corpus_offline" if is_demo else "html_text_strip",
        "content_origin": "local_demo_corpus" if is_demo else "live_web",
    }
    content = result.snippet
    if not is_demo:
        try:
            content = _fetch(result.url)
        except Exception as exc:  # noqa: BLE001 - one bad page must not kill a run
            logger.warning("fetch failed for %s: %s", result.url, exc)
            provenance["fetch_error"] = str(exc)[:200]
            provenance["extraction_method"] = "snippet_fallback"
    return Evidence(
        query_id=query_id,
        query_text=query_text,
        provider=result.provider,
        provider_rank=result.rank,
        url=result.url,
        title=result.title,
        snippet=result.snippet,
        content=content,
        content_chars=len(content),
        provenance=provenance,
    )
