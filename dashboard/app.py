"""Streamlit UI: pipeline explorer + grounded (cited) answers.

Run:  streamlit run dashboard/app.py
"""

import pathlib
import sys

import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.assess.scorer import lexical_relevance, split_sentences  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402

st.set_page_config(page_title="Grounded Evidence Pipeline", layout="wide")

st.title("Grounded Evidence Pipeline")
st.caption(
    "Search -> extract -> score -> store -> evaluate. Every record carries full "
    "provenance. Demo mode runs fully offline on the local corpus."
)

tab_explore, tab_answers = st.tabs(["Pipeline Explorer", "Grounded Answers (no LLM)"])

with tab_explore:
    query = st.text_input("Query", "How does Kenya regulate AI and personal data?")
    top_k = st.slider("Top K", 1, 10, 5)
    if st.button("Run pipeline"):
        with st.spinner("Running search -> extract -> score -> store..."):
            result = run_pipeline(query, top_k=top_k)
        m = result["metrics"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Evidence collected", m["n_evidence"])
        c2.metric("precision@k", m["precision_at_k"])
        c3.metric("grounded rate", m["grounded_rate"])
        c4.metric("provenance coverage", m["provenance_coverage"])

        rows = result["evidence"]
        st.dataframe(
            [
                {
                    "score": r["relevance_score"],
                    "grounded": bool(r["grounded"]),
                    "title": r["title"],
                    "url": r["url"],
                    "extracted_at": r["extracted_at"],
                }
                for r in rows
            ],
            use_container_width=True,
        )
        for r in rows:
            with st.expander(f"[{r['relevance_score']:.2f}] {r['title']}"):
                st.write(r["snippet"])
                st.caption("Provenance")
                st.json(r["provenance_json"])

        report_file = pathlib.Path(result["report_path"])
        if report_file.exists():
            st.download_button(
                "Download evaluation report (markdown)",
                data=report_file.read_text(encoding="utf-8"),
                file_name="evaluation_report.md",
                mime="text/markdown",
            )

with tab_answers:
    st.markdown(
        "Retrieves evidence, ranks sentences by support, and cites sources. "
        "This is the extractive baseline for a grounded answer - swap in an LLM "
        "via `src/assess/scorer.llm_score_hook` for generative answers."
    )
    question = st.text_input(
        "Ask a question", "What drives e-commerce growth in East Africa?"
    )
    if st.button("Get grounded answer"):
        result = run_pipeline(question, top_k=5)
        rows = [r for r in result["evidence"] if r["relevance_score"] > 0]
        ranked = []
        for r in rows:
            for sentence in split_sentences(r["snippet"]):
                support = lexical_relevance(question, sentence)
                if support > 0:
                    ranked.append((support, sentence, r["url"], r["title"]))
        ranked.sort(key=lambda t: t[0], reverse=True)
        top = ranked[:3]

        if top:
            st.markdown("### Answer (extractive, with citations)")
            st.markdown(" ".join(f"{t[1]} [{i + 1}]" for i, t in enumerate(top)))
            st.markdown("**Sources**")
            for i, t in enumerate(top, 1):
                st.markdown(f"{i}. [{t[3]}]({t[2]})")
            st.caption(
                "Extractive demo: sentences are retrieved and cited directly from "
                "the evidence store - nothing is generated."
            )
        else:
            st.warning(
                "No supporting evidence found for this question in the demo corpus. "
                "Try the sample question, or add documents to sample_corpus/."
            )
