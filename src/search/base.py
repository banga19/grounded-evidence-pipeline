"""Search provider interface.

Every provider returns the same SearchResult shape, so the rest of the
pipeline never needs to know where results came from. This abstraction is
what lets the demo run offline today and switch to Azure AI Foundry
"Grounding with Bing" later without touching pipeline code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """One raw search hit, before extraction and scoring."""

    title: str
    url: str
    snippet: str
    rank: int
    provider: str


class SearchProvider(ABC):
    """A provider turns a query into ranked SearchResults."""

    name: str = "base"

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list:
        """Return up to top_k SearchResult objects for the query."""
        raise NotImplementedError
