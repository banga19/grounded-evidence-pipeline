"""Assessment layer: is this evidence relevant, and is an answer grounded?

Two scores power the demo:

- lexical_relevance(): token overlap between query and retrieved content.
  Fast, explainable, zero cost - the baseline every fancier method must be
  measured against.
- groundedness(): the share of an answer's sentences actually supported by
  the evidence text. This is what enterprise buyers mean when they say a
  system is "grounded", and it is the hook where an LLM judge plugs in.

llm_score_hook() is the marked TODO for Azure OpenAI / Claude scoring,
with cost and latency logging so tradeoffs can be reported, not guessed.
"""

import os

from ..common.text import split_sentences, tokens


def lexical_relevance(query: str, content: str, snippet: str = "") -> float:
    """Share of query tokens found in content + snippet. 1.0 = full coverage."""
    q = tokens(query)
    if not q:
        return 0.0
    body = tokens(content) | tokens(snippet)
    return round(len(q & body) / len(q), 3)


def _sentence_support(sentence: str, evidence_text: str, min_overlap: float = 0.5) -> bool:
    s_tokens = tokens(sentence)
    if not s_tokens:
        return False
    overlap = len(s_tokens & tokens(evidence_text)) / len(s_tokens)
    return overlap >= min_overlap


def groundedness(answer: str, evidence_text: str) -> float:
    """Fraction of answer sentences with token support in the evidence text."""
    sentences = [s for s in split_sentences(answer) if len(s.split()) > 3]
    if not sentences:
        return 0.0
    supported = sum(1 for s in sentences if _sentence_support(s, evidence_text))
    return round(supported / len(sentences), 3)


def llm_score_hook(evidence):
    """Optional LLM-judge hook. Returns None until an LLM is configured,
    in which case the pipeline keeps the lexical score.

    TODO(banga19): call Azure OpenAI / Claude with a rubric prompt:
    'Rate 0-1 how well this source answers the query. Return JSON only.'
    Log tokens and latency per call so cost/latency is measured, not guessed.
    """
    if not os.environ.get("LLM_SCORER_ENABLED"):
        return None
    raise NotImplementedError("LLM scoring is a marked TODO - see README roadmap.")
