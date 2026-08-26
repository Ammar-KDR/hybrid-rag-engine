from time import perf_counter

from sentence_transformers import CrossEncoder

from rag.ingestion.pipeline import build_chunks

from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.retrieval.fusion import ReciprocalRankFusion

from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore

from rag.reranking.reranker import CrossEncoderReranker

from rag.evaluation.evaluator import RetrievalEvaluator
from rag.evaluation.dataset import load_evaluation_dataset


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "data/evaluation/hybrid_retrieval_dataset.json"

# Use the collection containing the expanded ~262 chunk corpus.
# Change this if your current collection has a different name.
COLLECTION_NAME = "documents3"

CANDIDATE_K = 20
FINAL_K = 5

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


# ============================================================
# TIMED RETRIEVER
# ============================================================

class TimedRetriever:
    """
    Wraps a normal retriever and measures retrieval latency.

    It preserves the normal:
        retrieve(query, top_k)
    contract expected by RetrievalEvaluator.
    """

    def __init__(self, retriever):
        self.retriever = retriever
        self.latencies = []

    def retrieve(self, query: str, top_k: int = 5):

        start = perf_counter()

        results = self.retriever.retrieve(
            query=query,
            top_k=top_k,
        )

        elapsed_ms = (
            perf_counter() - start
        ) * 1000

        self.latencies.append(elapsed_ms)

        return results

    def average_latency_ms(self):

        if not self.latencies:
            return 0.0

        return (
            sum(self.latencies)
            / len(self.latencies)
        )


# ============================================================
# RERANKED RETRIEVER
# ============================================================

class RerankedRetriever:
    """
    Evaluation wrapper implementing:

        query
          ↓
        first-stage retriever
          ↓
        candidate_k candidates
          ↓
        cross-encoder reranker
          ↓
        final top_k

    It also separately measures:
        - candidate retrieval latency
        - reranker latency
        - total latency
    """

    def __init__(
        self,
        retriever,
        reranker,
        candidate_k: int = 20,
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.candidate_k = candidate_k

        self.retrieval_latencies = []
        self.reranker_latencies = []
        self.total_latencies = []

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ):

        total_start = perf_counter()

        # ----------------------------------------------------
        # Stage 1 — Candidate Retrieval
        # ----------------------------------------------------

        retrieval_start = perf_counter()

        candidates = self.retriever.retrieve(
            query=query,
            top_k=self.candidate_k,
        )

        retrieval_ms = (
            perf_counter() - retrieval_start
        ) * 1000

        # ----------------------------------------------------
        # Stage 2 — Cross-Encoder Reranking
        # ----------------------------------------------------

        reranker_start = perf_counter()

        reranked_results = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
        )

        reranker_ms = (
            perf_counter() - reranker_start
        ) * 1000

        # ----------------------------------------------------
        # Total
        # ----------------------------------------------------

        total_ms = (
            perf_counter() - total_start
        ) * 1000

        self.retrieval_latencies.append(
            retrieval_ms
        )

        self.reranker_latencies.append(
            reranker_ms
        )

        self.total_latencies.append(
            total_ms
        )

        return reranked_results

    def average_retrieval_latency_ms(self):

        if not self.retrieval_latencies:
            return 0.0

        return (
            sum(self.retrieval_latencies)
            / len(self.retrieval_latencies)
        )

    def average_reranker_latency_ms(self):

        if not self.reranker_latencies:
            return 0.0

        return (
            sum(self.reranker_latencies)
            / len(self.reranker_latencies)
        )

    def average_total_latency_ms(self):

        if not self.total_latencies:
            return 0.0

        return (
            sum(self.total_latencies)
            / len(self.total_latencies)
        )


# ============================================================
# NORMAL RETRIEVER EVALUATION
# ============================================================

def evaluate_retriever(
    name,
    retriever,
    dataset,
    k=5,
):

    evaluator = RetrievalEvaluator(
        retriever=retriever
    )

    results = evaluator.evaluate(
        dataset,
        k=k
    )

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print(
        f"Hit Rate@{k}: "
        f"{results['hit_rate']:.2f}"
    )

    print(
        f"Recall@{k}: "
        f"{results['recall_rate']:.2f}"
    )

    print(
        f"Precision@{k}: "
        f"{results['avg_precision']:.2f}"
    )

    print(
        f"MRR@{k}: "
        f"{results['mrr_score']:.2f}"
    )

    return results


# ============================================================
# CANDIDATE-STAGE EVALUATION
# ============================================================

def evaluate_candidate_stage(
    name,
    retriever,
    dataset,
):

    evaluator = RetrievalEvaluator(
        retriever=retriever
    )

    results = evaluator.evaluate(
        dataset,
        k=CANDIDATE_K
    )

    print("\n" + "=" * 70)
    print(
        f"{name} — CANDIDATE STAGE"
    )
    print("=" * 70)

    print(
        f"Hit Rate@{CANDIDATE_K}: "
        f"{results['hit_rate']:.2f}"
    )

    print(
        f"Recall@{CANDIDATE_K}: "
        f"{results['recall_rate']:.2f}"
    )

    print(
        "\nQuestion answered:"
    )

    print(
        "Did the correct evidence reach "
        "the reranker candidate pool?"
    )

    return results


# ============================================================
# HIT COMPARISON
# ============================================================

def analyze_hit_changes(
    baseline_name,
    baseline_results,
    reranked_name,
    reranked_results,
):

    improved = []
    hurt = []
    unchanged_hit = []
    unchanged_miss = []

    for baseline_item, reranked_item in zip(
        baseline_results["results"],
        reranked_results["results"],
    ):

        question = baseline_item["question"]

        before = baseline_item["hit"]
        after = reranked_item["hit"]

        if not before and after:
            improved.append(question)

        elif before and not after:
            hurt.append(question)

        elif before and after:
            unchanged_hit.append(question)

        else:
            unchanged_miss.append(question)

    print("\n")
    print("=" * 70)
    print(
        f"HIT ANALYSIS: "
        f"{baseline_name} → {reranked_name}"
    )
    print("=" * 70)

    print("\nIMPROVED")
    print("-" * 30)

    if improved:
        for question in improved:
            print(
                f"+ {question}"
            )
    else:
        print("None")

    print("\nHURT")
    print("-" * 30)

    if hurt:
        for question in hurt:
            print(
                f"- {question}"
            )
    else:
        print("None")

    print("\nSTILL HIT")
    print("-" * 30)
    print(
        len(unchanged_hit)
    )

    print("\nSTILL MISS")
    print("-" * 30)

    if unchanged_miss:
        for question in unchanged_miss:
            print(
                f"- {question}"
            )
    else:
        print("None")

def analyze_rank_movements(
    name,
    baseline_retriever,
    reranked_retriever,
    dataset,
    candidate_k=20,
    final_k=5,
):

    print("\n")
    print("=" * 90)
    print(f"RANK MOVEMENT ANALYSIS: {name}")
    print("=" * 90)

    improvements = []
    regressions = []
    unchanged = []
    candidate_misses = []

    for case in dataset:

        # Support either dictionaries or dataclass-style objects
        if isinstance(case, dict):
            question = case["question"]
            expected_ids = set(
                case["expected_chunk_ids"]
            )
        else:
            question = case.question
            expected_ids = set(
                case.expected_chunk_ids
            )

        # --------------------------------------------------
        # BEFORE RERANKING
        # Retrieve 20 so we can observe cases such as 8 -> 2
        # --------------------------------------------------

        baseline_results = baseline_retriever.retrieve(
            query=question,
            top_k=candidate_k,
        )

        original_rank = None

        for rank, result in enumerate(
            baseline_results,
            start=1,
        ):
            if result.chunk_id in expected_ids:
                original_rank = rank
                break

        # --------------------------------------------------
        # AFTER RERANKING
        #
        # Ask for all 20 reranked candidates so we can see
        # actual rank movement rather than only top-5 hits.
        # --------------------------------------------------

        reranked_results = reranked_retriever.retrieve(
            query=question,
            top_k=candidate_k,
        )

        reranked_rank = None

        for rank, result in enumerate(
            reranked_results,
            start=1,
        ):
            if result.chunk_id in expected_ids:
                reranked_rank = rank
                break

        # --------------------------------------------------
        # Candidate-stage miss
        # --------------------------------------------------

        if original_rank is None:

            candidate_misses.append(
                {
                    "question": question,
                    "before": None,
                    "after": reranked_rank,
                }
            )

            continue

        # --------------------------------------------------
        # Rank movement
        # --------------------------------------------------

        movement = (
            original_rank - reranked_rank
            if reranked_rank is not None
            else None
        )

        record = {
            "question": question,
            "before": original_rank,
            "after": reranked_rank,
            "movement": movement,
        }

        if reranked_rank is None:
            regressions.append(record)

        elif reranked_rank < original_rank:
            improvements.append(record)

        elif reranked_rank > original_rank:
            regressions.append(record)

        else:
            unchanged.append(record)

    # ------------------------------------------------------
    # Sort most dramatic movements first
    # ------------------------------------------------------

    improvements.sort(
        key=lambda x: x["movement"],
        reverse=True,
    )

    regressions.sort(
        key=lambda x: (
            x["movement"]
            if x["movement"] is not None
            else -999
        )
    )

    # ------------------------------------------------------
    # Print Improvements
    # ------------------------------------------------------

    print("\nIMPROVED RANKING")
    print("-" * 90)

    if not improvements:
        print("None")
    else:
        for item in improvements:

            print(
                f"{item['before']:>2} -> "
                f"{item['after']:<2} | "
                f"{item['question']}"
            )

    # ------------------------------------------------------
    # Print Regressions
    # ------------------------------------------------------

    print("\nWORSENED RANKING")
    print("-" * 90)

    if not regressions:
        print("None")
    else:
        for item in regressions:

            after = (
                item["after"]
                if item["after"] is not None
                else "MISS"
            )

            print(
                f"{item['before']:>2} -> "
                f"{str(after):<4} | "
                f"{item['question']}"
            )

    # ------------------------------------------------------
    # Unchanged
    # ------------------------------------------------------

    print("\nUNCHANGED RANK")
    print("-" * 90)

    print(
        f"{len(unchanged)} questions"
    )

    # ------------------------------------------------------
    # Candidate misses
    # ------------------------------------------------------

    print("\nNOT FOUND IN ORIGINAL TOP "
          f"{candidate_k}")
    print("-" * 90)

    if not candidate_misses:
        print("None")
    else:
        for item in candidate_misses:
            print(
                f"- {item['question']}"
            )

    # ------------------------------------------------------
    # Top-5 impact summary
    # ------------------------------------------------------

    rescued_into_top5 = []
    pushed_out_of_top5 = []

    for item in improvements:

        if (
            item["before"] > final_k
            and item["after"] <= final_k
        ):
            rescued_into_top5.append(item)

    for item in regressions:

        if (
            item["before"] <= final_k
            and (
                item["after"] is None
                or item["after"] > final_k
            )
        ):
            pushed_out_of_top5.append(item)

    print("\nTOP-5 RESCUES")
    print("-" * 90)

    if not rescued_into_top5:
        print("None")
    else:
        for item in rescued_into_top5:
            print(
                f"{item['before']} -> "
                f"{item['after']} | "
                f"{item['question']}"
            )

    print("\nPUSHED OUT OF TOP-5")
    print("-" * 90)

    if not pushed_out_of_top5:
        print("None")
    else:
        for item in pushed_out_of_top5:
            print(
                f"{item['before']} -> "
                f"{item['after']} | "
                f"{item['question']}"
            )


# ============================================================
# FINAL COMPARISON TABLE
# ============================================================

def print_final_comparison(
    dense_results,
    bm25_results,
    hybrid_results,
    dense_reranked_results,
    hybrid_reranked_results,
    dense_timed,
    bm25_timed,
    hybrid_timed,
    dense_reranked,
    hybrid_reranked,
):

    rows = [
        (
            "Dense",
            dense_results,
            dense_timed.average_latency_ms(),
        ),
        (
            "BM25",
            bm25_results,
            bm25_timed.average_latency_ms(),
        ),
        (
            "Hybrid",
            hybrid_results,
            hybrid_timed.average_latency_ms(),
        ),
        (
            "Dense + Reranker",
            dense_reranked_results,
            dense_reranked.average_total_latency_ms(),
        ),
        (
            "Hybrid + Reranker",
            hybrid_reranked_results,
            hybrid_reranked.average_total_latency_ms(),
        ),
    ]

    print("\n\n")
    print("=" * 100)
    print("FINAL RETRIEVAL ARCHITECTURE COMPARISON")
    print("=" * 100)

    print(
        f"{'Architecture':<24}"
        f"{'Hit@5':>10}"
        f"{'Recall@5':>12}"
        f"{'Precision@5':>15}"
        f"{'MRR@5':>10}"
        f"{'Latency ms':>15}"
    )

    print("-" * 100)

    for name, result, latency in rows:

        print(
            f"{name:<24}"
            f"{result['hit_rate']:>10.2f}"
            f"{result['recall_rate']:>12.2f}"
            f"{result['avg_precision']:>15.2f}"
            f"{result['mrr_score']:>10.2f}"
            f"{latency:>15.2f}"
        )


# ============================================================
# RERANKER LATENCY DETAILS
# ============================================================

def print_reranker_latency(
    name,
    retriever,
):

    print("\n" + "=" * 70)
    print(
        f"{name} LATENCY BREAKDOWN"
    )
    print("=" * 70)

    print(
        "Candidate retrieval avg: "
        f"{retriever.average_retrieval_latency_ms():.2f} ms"
    )

    print(
        "Reranker avg: "
        f"{retriever.average_reranker_latency_ms():.2f} ms"
    )

    print(
        "Total avg: "
        f"{retriever.average_total_latency_ms():.2f} ms"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Evaluation Dataset
    # --------------------------------------------------------

    dataset = load_evaluation_dataset(
        DATASET_PATH
    )


    # --------------------------------------------------------
    # Shared Dense Infrastructure
    # --------------------------------------------------------

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore()

    dense_retriever = DenseRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
        collection_name=COLLECTION_NAME,
    )


    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    chunks = build_chunks()

    bm25_retriever = BM25Retriever(
        chunks
    )


    # --------------------------------------------------------
    # Hybrid
    # --------------------------------------------------------
    #
    # candidate_k=20 here deliberately.
    #
    # This means Hybrid and Hybrid + Reranker use the same
    # first-stage candidate-generation configuration.
    #
    # That isolates the effect of reranking more fairly.
    # --------------------------------------------------------

    hybrid_fusion = ReciprocalRankFusion(
        k=60
    )

    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        fusion=hybrid_fusion,
        candidate_k=CANDIDATE_K,
    )


    # --------------------------------------------------------
    # Cross-Encoder
    # --------------------------------------------------------

    print("\nLoading cross-encoder...")

    cross_encoder = CrossEncoder(
        RERANKER_MODEL
    )

    reranker = CrossEncoderReranker(
        cross_encoder
    )


    # --------------------------------------------------------
    # Warm Up Cross-Encoder
    # --------------------------------------------------------
    #
    # Avoid including first-inference initialization effects
    # in the reranking latency measurements.
    # --------------------------------------------------------

    cross_encoder.predict(
        [
            (
                "warmup query",
                "warmup technical documentation passage",
            )
        ]
    )


    # --------------------------------------------------------
    # Candidate Recall Evaluation
    # --------------------------------------------------------
    #
    # These answer:
    #
    # Did relevant evidence reach the top-20 pool?
    # --------------------------------------------------------

    dense_candidate_results = (
        evaluate_candidate_stage(
            "Dense",
            dense_retriever,
            dataset,
        )
    )

    hybrid_candidate_results = (
        evaluate_candidate_stage(
            "Hybrid",
            hybrid_retriever,
            dataset,
        )
    )


    # --------------------------------------------------------
    # Timed Baseline Retrievers
    # --------------------------------------------------------

    dense_timed = TimedRetriever(
        dense_retriever
    )

    bm25_timed = TimedRetriever(
        bm25_retriever
    )

    hybrid_timed = TimedRetriever(
        hybrid_retriever
    )


    # --------------------------------------------------------
    # Reranked Architectures
    # --------------------------------------------------------

    dense_reranked = RerankedRetriever(
        retriever=dense_retriever,
        reranker=reranker,
        candidate_k=CANDIDATE_K,
    )

    hybrid_reranked = RerankedRetriever(
        retriever=hybrid_retriever,
        reranker=reranker,
        candidate_k=CANDIDATE_K,
    )


    # --------------------------------------------------------
    # Final @5 Evaluation
    # --------------------------------------------------------

    dense_results = evaluate_retriever(
        "Dense Retriever",
        dense_timed,
        dataset,
        k=FINAL_K,
    )


    bm25_results = evaluate_retriever(
        "BM25 Retriever",
        bm25_timed,
        dataset,
        k=FINAL_K,
    )


    hybrid_results = evaluate_retriever(
        "Hybrid Retriever",
        hybrid_timed,
        dataset,
        k=FINAL_K,
    )


    dense_reranked_results = evaluate_retriever(
        "Dense + Cross-Encoder Reranker",
        dense_reranked,
        dataset,
        k=FINAL_K,
    )


    hybrid_reranked_results = evaluate_retriever(
        "Hybrid + Cross-Encoder Reranker",
        hybrid_reranked,
        dataset,
        k=FINAL_K,
    )


    # --------------------------------------------------------
    # Candidate Recall Summary
    # --------------------------------------------------------

    print("\n\n")
    print("=" * 70)
    print("CANDIDATE RECALL SUMMARY")
    print("=" * 70)

    print(
        f"Dense Recall@{CANDIDATE_K}: "
        f"{dense_candidate_results['recall_rate']:.2f}"
    )

    print(
        f"Hybrid Recall@{CANDIDATE_K}: "
        f"{hybrid_candidate_results['recall_rate']:.2f}"
    )


    # --------------------------------------------------------
    # Reranking Hit Analysis
    # --------------------------------------------------------

    analyze_hit_changes(
        "Dense",
        dense_results,
        "Dense + Reranker",
        dense_reranked_results,
    )

    analyze_hit_changes(
        "Hybrid",
        hybrid_results,
        "Hybrid + Reranker",
        hybrid_reranked_results,
    )


    # --------------------------------------------------------
    # Detailed Reranker Latency
    # --------------------------------------------------------

    print_reranker_latency(
        "DENSE + RERANKER",
        dense_reranked,
    )

    print_reranker_latency(
        "HYBRID + RERANKER",
        hybrid_reranked,
    )


    # --------------------------------------------------------
    # Final Comparison
    # --------------------------------------------------------

    print_final_comparison(
        dense_results=dense_results,
        bm25_results=bm25_results,
        hybrid_results=hybrid_results,
        dense_reranked_results=dense_reranked_results,
        hybrid_reranked_results=hybrid_reranked_results,
        dense_timed=dense_timed,
        bm25_timed=bm25_timed,
        hybrid_timed=hybrid_timed,
        dense_reranked=dense_reranked,
        hybrid_reranked=hybrid_reranked,
    )

        # --------------------------------------------------------
    # Rank Movement Failure Analysis
    # --------------------------------------------------------

    analyze_rank_movements(
        name="Dense → Dense + Reranker",
        baseline_retriever=dense_retriever,
        reranked_retriever=dense_reranked,
        dataset=dataset,
        candidate_k=CANDIDATE_K,
        final_k=FINAL_K,
    )

    analyze_rank_movements(
        name="Hybrid → Hybrid + Reranker",
        baseline_retriever=hybrid_retriever,
        reranked_retriever=hybrid_reranked,
        dataset=dataset,
        candidate_k=CANDIDATE_K,
        final_k=FINAL_K,
    )


if __name__ == "__main__":
    main()