import time
from pathlib import Path
from dataclasses import dataclass

from rag.config import settings
from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore
from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.fusion import ReciprocalRankFusion
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.reranking.reranker import CrossEncoderReranker
from sentence_transformers import CrossEncoder
from rag.ingestion.chunk_store import ChunkStore
from rag.evaluation.golden_dataset import load_golden_dataset
from rag.evaluation.retrieval_evidence_evaluator import RetrievalEvidenceEvaluator


def evaluate_retriever_pipeline(limit: int | None = None):
    print("=" * 80)
    print(" [INFORMATION RETRIEVAL EVALUATION] HitRate@5, Recall@5, Precision@5, MRR@5")
    print("=" * 80)

    # 1. Load dataset
    dataset_path = Path("data/evaluation/day10_golden_rag_dataset_v1.json")
    all_cases = load_golden_dataset(dataset_path)
    # Filter answerable cases with expected sources
    cases = [c for c in all_cases if c.answerable and c.expected_sources]
    if limit:
        cases = cases[:limit]
    print(f"Loaded {len(cases)} answerable evaluation cases with ground truth evidence.")

    # 2. Setup retrievers
    embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL_NAME)
    if settings.QDRANT_STORAGE_MODE == "local":
        vector_store = QdrantVectorStore(path=settings.QDRANT_LOCAL_PATH)
    else:
        vector_store = QdrantVectorStore(url=settings.QDRANT_URL)

    dense_retriever = DenseRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
        collection_name=settings.QDRANT_COLLECTION,
    )

    chunk_store = ChunkStore(settings.CHUNK_STORE_PATH)
    chunks = chunk_store.load_all()
    bm25_retriever = BM25Retriever(chunks=chunks)

    rrf = ReciprocalRankFusion(k=60)
    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        fusion=rrf,
        candidate_k=20,
    )

    cross_encoder = CrossEncoderReranker(
        model=CrossEncoder(settings.RERANKER_MODEL_NAME)
    )

    evaluator = RetrievalEvidenceEvaluator()

    architectures = {
        "Dense (MiniLM)": lambda q: dense_retriever.retrieve(query=q, top_k=5),
        "BM25 (Lexical)": lambda q: bm25_retriever.retrieve(query=q, top_k=5),
        "Hybrid (Dense+BM25+RRF)": lambda q: hybrid_retriever.retrieve(query=q, top_k=5),
        "Hybrid + Reranker (bge)": lambda q: cross_encoder.rerank(
            query=q,
            candidates=hybrid_retriever.retrieve(query=q, top_k=20),
            top_k=5,
        ),
    }

    results = {}

    for name, retrieve_fn in architectures.items():
        print(f"\nEvaluating: {name} ...")
        hit_list = []
        source_recall_list = []
        evidence_recall_list = []
        precision_list = []
        mrr_list = []
        latencies = []

        for case in cases:
            start = time.perf_counter()
            top_chunks = retrieve_fn(case.question)
            lat_ms = (time.perf_counter() - start) * 1000
            latencies.append(lat_ms)

            # Evaluate top-5 chunks against ground truth
            stage_eval = evaluator._evaluate_stage(case=case, chunks=top_chunks)

            hit_list.append(1.0 if stage_eval.hit else 0.0)
            source_recall_list.append(stage_eval.source_recall or 0.0)
            evidence_recall_list.append(stage_eval.evidence_span_recall or 0.0)
            mrr_list.append(stage_eval.mrr or 0.0)

            # Precision@5: how many of the top 5 chunks matched an expected source or evidence span
            relevant_in_top5 = 0
            for chunk in top_chunks:
                matched_source = any(
                    evaluator._matches_expected_source(chunk, exp)
                    for exp in case.expected_sources
                )
                matched_span = any(
                    evaluator._matches_evidence_span(chunk, span)
                    for span in case.evidence_spans
                )
                if matched_source or matched_span:
                    relevant_in_top5 += 1
            precision_list.append(relevant_in_top5 / max(len(top_chunks), 1))

        n = len(cases)
        results[name] = {
            "hit_rate": sum(hit_list) / n,
            "source_recall": sum(source_recall_list) / n,
            "evidence_recall": sum(evidence_recall_list) / n,
            "precision": sum(precision_list) / n,
            "mrr": sum(mrr_list) / n,
            "avg_latency_ms": sum(latencies) / n,
        }

    # Print clean comparison table (ASCII safe for Windows cp1252)
    print("\n" + "=" * 90)
    print(" FINAL RETRIEVAL BENCHMARK COMPARISON TABLE")
    print("=" * 90)
    print(f"{'Architecture':<26} | {'Hit@5':>8} | {'Recall@5':>10} | {'Precision@5':>12} | {'MRR@5':>8} | {'Latency':>10}")
    print("-" * 90)

    for name, m in results.items():
        print(
            f"{name:<26} | "
            f"{m['hit_rate']:>7.2%} | "
            f"{m['evidence_recall']:>9.2%} | "
            f"{m['precision']:>11.2%} | "
            f"{m['mrr']:>8.3f} | "
            f"{m['avg_latency_ms']:>8.1f} ms"
        )
    print("=" * 90)

    return results


if __name__ == "__main__":
    evaluate_retriever_pipeline(limit=30)
