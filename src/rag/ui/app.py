import streamlit as st
import pandas as pd
import os
from rag.ui.client import RAGAPIClient
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# Page configuration
# =========================================================

st.set_page_config(
    page_title="Hybrid RAG Inspector",
    page_icon="🔎",
    layout="wide",
)

url=os.getenv("API_BASE_URL")
client = RAGAPIClient(
    base_url=url
)


# =========================================================
# Header
# =========================================================

st.title(
    "Hybrid RAG Inspection UI"
)

st.caption(
    "Inspect answers, citations, retrieval, "
    "verification, latency, and ingestion."
)


# =========================================================
# Sidebar — ingestion
# =========================================================

with st.sidebar:

    st.header("Knowledge Base")

    uploaded_file = st.file_uploader(
        "Upload document",
        type=[
            "md",
            "txt",
            "pdf",
            "html",
            "htm",
        ],
    )

    if (
        uploaded_file is not None
        and st.button(
            "Ingest document",
            use_container_width=True,
        )
    ):

        try:
            result = client.ingest(
                filename=(
                    uploaded_file.name
                ),
                content=(
                    uploaded_file.getvalue()
                ),
            )

            if result["duplicate"]:
                st.warning(
                    "Document already exists."
                )
            else:
                st.success(
                    "Document ingested."
                )

            st.json(result)

        except Exception as exc:
            st.error(
                str(exc)
            )


    st.divider()

    if st.button(
        "Refresh documents",
        use_container_width=True,
    ):

        try:
            st.session_state[
                "documents"
            ] = client.list_documents()

        except Exception as exc:
            st.error(
                str(exc)
            )


    documents = st.session_state.get(
        "documents",
        []
    )

    st.metric(
        "Registered documents",
        len(documents),
    )

    for document in documents:
        with st.expander(
            document["filename"]
        ):
            st.write(
                f"**Type:** "
                f"{document['file_type']}"
            )

            st.write(
                f"**Chunks:** "
                f"{document['chunk_count']}"
            )

            st.write(
                f"**Strategy:** "
                f"{document['chunking_strategy']}"
            )

            st.caption(
                document["document_id"]
            )


# =========================================================
# Query controls
# =========================================================

question = st.text_area(
    "Question",
    placeholder=(
        "Ask something about your knowledge base..."
    ),
    height=100,
)

include_trace = st.checkbox(
    "Include retrieval trace",
    value=True,
)


ask_clicked = st.button(
    "Ask",
    type="primary",
)


# =========================================================
# Ask API
# =========================================================

if ask_clicked:

    if not question.strip():
        st.warning(
            "Enter a question first."
        )

    else:

        try:
            with st.spinner(
                "Running RAG pipeline..."
            ):
                result = client.ask(
                    question=question,
                    include_trace=include_trace,
                )

            st.session_state[
                "last_result"
            ] = result

        except Exception as exc:
            st.error(
                str(exc)
            )


result = st.session_state.get(
    "last_result"
)


if result:

    st.divider()


    # =====================================================
    # Answer
    # =====================================================

    st.subheader("Answer")

    if result["abstained"]:
        st.warning(
            "The system abstained."
        )
    else:
        st.success(
            "Answer accepted."
        )

    st.markdown(
        result["answer"]
    )

    st.caption(
        f"Request ID: "
        f"{result['request_id']}"
    )


    # =====================================================
    # Citations
    # =====================================================

    st.subheader("Citations")

    if not result["citations"]:
        st.info(
            "No citations returned."
        )

    else:

        for citation in result[
            "citations"
        ]:

            with st.expander(
                f"[{citation['reference']}] "
                f"{citation['source']}"
            ):

                st.write(
                    "**Chunk ID:**",
                    citation["chunk_id"],
                )

                if (
                    citation[
                        "page_number"
                    ]
                    is not None
                ):
                    st.write(
                        "**Page:**",
                        citation[
                            "page_number"
                        ],
                    )

                if citation[
                    "heading_path"
                ]:
                    st.write(
                        "**Heading:**",
                        " → ".join(
                            citation[
                                "heading_path"
                            ]
                        ),
                    )


    # =====================================================
    # Latency
    # =====================================================

    st.subheader(
        "Performance"
    )

    latency = result[
        "latency"
    ]

    columns = st.columns(5)

    columns[0].metric(
        "Retrieval",
        f"{latency['retrieval_ms']:.0f} ms",
    )

    columns[1].metric(
        "Reranking",
        f"{latency['reranking_ms']:.0f} ms",
    )

    columns[2].metric(
        "Generation",
        f"{latency['generation_ms']:.0f} ms",
    )

    columns[3].metric(
        "Verification",
        f"{latency['verification_ms']:.0f} ms",
    )

    columns[4].metric(
        "Total",
        f"{latency['total_ms']:.0f} ms",
    )


    # =====================================================
    # Token usage
    # =====================================================

    token_usage = result[
        "token_usage"
    ]

    st.subheader(
        "Token Usage"
    )

    token_columns = st.columns(3)

    token_columns[0].metric(
        "Input",
        token_usage[
            "input_tokens"
        ]
        or "N/A",
    )

    token_columns[1].metric(
        "Output",
        token_usage[
            "output_tokens"
        ]
        or "N/A",
    )

    token_columns[2].metric(
        "Total",
        token_usage[
            "total_tokens"
        ]
        or "N/A",
    )


    # =====================================================
    # Verification
    # =====================================================

    st.subheader(
        "Verification"
    )

    verification = result[
        "verification"
    ]

    metrics = verification[
        "citation_metrics"
    ]

    metric_columns = st.columns(2)

    metric_columns[0].metric(
        "Citation precision",
        (
            f"{metrics['citation_precision']:.2%}"
            if metrics[
                "citation_precision"
            ] is not None
            else "N/A"
        ),
    )

    metric_columns[1].metric(
        "Citation coverage",
        (
            f"{metrics['citation_coverage']:.2%}"
            if metrics[
                "citation_coverage"
            ] is not None
            else "N/A"
        ),
    )


    with st.expander(
        "Claims"
    ):

        for claim in verification[
            "claims"
        ]:

            st.write(
                claim["text"]
            )

            st.caption(
                f"Citations: "
                f"{claim['citations']}"
            )


    with st.expander(
        "Citation verification"
    ):

        for item in verification[
            "citation_verification"
        ]:

            st.write(
                f"**{item['verdict']}** — "
                f"{item['claim_text']}"
            )

            st.caption(
                item[
                    "explanation"
                ]
            )


    with st.expander(
        "Faithfulness"
    ):

        faithfulness = verification[
            "faithfulness"
        ]

        for item in faithfulness[
            "claims"
        ]:

            st.write(
                f"**{item['verdict']}** — "
                f"{item['claim_text']}"
            )

            st.caption(
                item[
                    "explanation"
                ]
            )


    # =====================================================
    # Retrieval trace
    # =====================================================

    trace = result.get(
        "trace"
    )

    if trace:

        st.subheader(
            "Retrieval Trace"
        )

        st.write(
            f"Candidates retrieved: "
            f"**{trace['candidate_count']}**"
        )

        st.write(
            f"Final evidence chunks: "
            f"**{trace['evidence_count']}**"
        )


        candidate_rows = []

        for candidate in trace[
            "candidates"
        ]:

            candidate_rows.append(
                {
                    "chunk_id": (
                        candidate[
                            "chunk_id"
                        ][:12]
                    ),
                    "source": (
                        candidate[
                            "source"
                        ]
                    ),
                    "RRF rank": (
                        candidate[
                            "rrf"
                        ][
                            "rank"
                        ]
                    ),
                    "RRF score": (
                        candidate[
                            "rrf"
                        ][
                            "score"
                        ]
                    ),
                    "Dense rank": (
                        candidate[
                            "dense"
                        ][
                            "rank"
                        ]
                        if candidate[
                            "dense"
                        ]
                        else None
                    ),
                    "BM25 rank": (
                        candidate[
                            "bm25"
                        ][
                            "rank"
                        ]
                        if candidate[
                            "bm25"
                        ]
                        else None
                    ),
                }
            )


        st.markdown(
            "#### Candidate retrieval"
        )

        st.dataframe(
            pd.DataFrame(
                candidate_rows
            ),
            use_container_width=True,
            hide_index=True,
        )


        evidence_rows = []

        for chunk in trace[
            "final_evidence"
        ]:

            evidence_rows.append(
                {
                    "chunk_id": (
                        chunk[
                            "chunk_id"
                        ][:12]
                    ),
                    "source": (
                        chunk[
                            "source"
                        ]
                    ),
                    "retrieval rank": (
                        chunk[
                            "retrieval"
                        ][
                            "rank"
                        ]
                    ),
                    "reranker rank": (
                        chunk[
                            "reranker"
                        ][
                            "rank"
                        ]
                    ),
                    "final rank": (
                        chunk[
                            "final"
                        ][
                            "rank"
                        ]
                    ),
                    "final score": (
                        chunk[
                            "final"
                        ][
                            "score"
                        ]
                    ),
                }
            )


        st.markdown(
            "#### Final evidence"
        )

        st.dataframe(
            pd.DataFrame(
                evidence_rows
            ),
            use_container_width=True,
            hide_index=True,
        )


        with st.expander(
            "Inspect candidate text"
        ):

            for candidate in trace[
                "candidates"
            ]:

                st.markdown(
                    f"**{candidate['source']}**"
                )

                st.caption(
                    candidate[
                        "chunk_id"
                    ]
                )

                st.write(
                    candidate[
                        "text"
                    ]
                )

                st.divider()