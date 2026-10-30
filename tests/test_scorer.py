"""Run with:  pytest -q   OR   python tests/test_scorer.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.assess.scorer import groundedness, lexical_relevance
from src.common.text import split_sentences


def test_perfect_relevance_is_one():
    assert lexical_relevance("Kenya AI policy", "Kenya AI policy document") == 1.0


def test_disjoint_is_zero():
    assert lexical_relevance("rocket launch schedule", "bakery recipes and cake design") == 0.0


def test_partial_relevance_between_zero_and_one():
    score = lexical_relevance("e-commerce growth in Kenya", "mobile money drives e-commerce growth")
    assert 0.0 < score < 1.0


def test_groundedness_full_support():
    answer = "Kenya enforces data protection rules."
    evidence = "Kenya enforces data protection rules for AI systems."
    assert groundedness(answer, evidence) == 1.0


def test_groundedness_no_support():
    assert groundedness("The moon is made of cheese.", "Baking bread requires flour.") == 0.0


def test_split_sentences():
    assert len(split_sentences("One. Two. Three!")) == 3


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
