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
from rag.reranking.rank_fusion_reranker import RankFusionReranker

from rag.evaluation.evaluator import RetrievalEvaluator
from rag.evaluation.dataset import load_evaluation_dataset


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "data/evaluation/hybrid_retrieval_dataset.json"

# Make sure this is the collection containing the 262 chunks.
COLLECTION_NAME = "documents3"

CANDIDATE_K = 20
FINAL_K = 5

RERANKER_MODEL = (
    "BAAI/bge-reranker-base"
)

# Initial rank-fusion configuration.
# Do NOT tune yet.
RETRIEVAL_WEIGHT = 0.5
RERANKER_WEIGHT = 0.5
RANK_FUSION_K = 60


# ============================================================
# TIMED BASELINE RETRIEVER
# ============================================================

class TimedRetriever:
    """
    Measures normal retrieval latency while preserving the
    retrieve(query, top_k) interface expected by our evaluator.
    """

    def __init__(self, retriever):
        self.retriever = retriever
        self.latencies = []

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ):

        start = perf_counter()

        results = self.retriever.retrieve(
            query=query,
            top_k=top_k,
        )

        elapsed_ms = (
            perf_counter() - start
        ) * 1000

        self.latencies.append(
            elapsed_ms
        )

        return results

    def average_latency_ms(self):

        if not self.latencies:
            return 0.0

        return (
            sum(self.latencies)
            / len(self.latencies)
        )


# ============================================================
# TWO-STAGE RETRIEVAL WRAPPER
# ============================================================

class TwoStageRetriever:
    """
    Generic evaluation wrapper:

        query
          ↓
        candidate retriever
          ↓
        candidate_k results
          ↓
        reranking strategy
          ↓
        final top_k

    reranking_strategy can be either:

        CrossEncoderReranker

    or:

        RankFusionReranker
    """

    def __init__(
        self,
        retriever,
        reranking_strategy,
        candidate_k: int = 20,
    ):
        self.retriever = retriever
        self.reranking_strategy = (
            reranking_strategy
        )

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
        # Stage 2 — Reranking
        # ----------------------------------------------------

        reranker_start = perf_counter()

        results = (
            self.reranking_strategy.rerank(
                query=query,
                candidates=candidates,
                top_k=top_k,
            )
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

        return results

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
# STANDARD EVALUATION
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
        k=k,
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
# CANDIDATE RECALL
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
        k=CANDIDATE_K,
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

    return results


# ============================================================
# HIT ANALYSIS
# ============================================================

def analyze_hit_changes(
    baseline_name,
    baseline_results,
    new_name,
    new_results,
):

    improved = []
    hurt = []
    still_hit = []
    still_miss = []

    for baseline_item, new_item in zip(
        baseline_results["results"],
        new_results["results"],
    ):

        question = baseline_item[
            "question"
        ]

        before = baseline_item["hit"]
        after = new_item["hit"]

        if not before and after:
            improved.append(question)

        elif before and not after:
            hurt.append(question)

        elif before and after:
            still_hit.append(question)

        else:
            still_miss.append(question)

    print("\n")
    print("=" * 80)

    print(
        f"HIT ANALYSIS: "
        f"{baseline_name} → {new_name}"
    )

    print("=" * 80)

    print("\nIMPROVED")
    print("-" * 40)

    if improved:
        for question in improved:
            print(
                f"+ {question}"
            )
    else:
        print("None")

    print("\nHURT")
    print("-" * 40)

    if hurt:
        for question in hurt:
            print(
                f"- {question}"
            )
    else:
        print("None")

    print("\nSTILL HIT")
    print("-" * 40)
    print(
        len(still_hit)
    )

    print("\nSTILL MISS")
    print("-" * 40)

    if still_miss:
        for question in still_miss:
            print(
                f"- {question}"
            )
    else:
        print("None")


# ============================================================
# THREE-STAGE RANK MOVEMENT ANALYSIS
# ============================================================

def analyze_rank_fusion_movements(
    hybrid_retriever,
    rank_fusion_retriever,
    dataset,
):

    print("\n")
    print("=" * 110)
    print(
        "RANK MOVEMENT ANALYSIS: "
        "HYBRID → CROSS ENCODER → FINAL FUSION"
    )
    print("=" * 110)

    records = []

    for case in dataset:

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


        # ----------------------------------------------------
        # Original Hybrid Candidates
        # ----------------------------------------------------

        hybrid_candidates = (
            hybrid_retriever.retrieve(
                query=question,
                top_k=CANDIDATE_K,
            )
        )


        # ----------------------------------------------------
        # Rank-Fusion Results
        #
        # Request all candidates so we can inspect every rank.
        # ----------------------------------------------------

        fusion_results = (
            rank_fusion_retriever.retrieve(
                query=question,
                top_k=CANDIDATE_K,
            )
        )


        # ----------------------------------------------------
        # Find first relevant hybrid rank
        # ----------------------------------------------------

        original_rank = None

        for candidate in hybrid_candidates:

            if (
                candidate.chunk_id
                in expected_ids
            ):
                original_rank = (
                    candidate.rank
                )

                break


        # ----------------------------------------------------
        # Find first relevant result after fusion
        #
        # Because RerankedChunk now preserves:
        #
        # retrieval_rank
        # reranker_rank
        # final_rank
        # ----------------------------------------------------

        relevant_result = None

        for result in fusion_results:

            if (
                result.chunk_id
                in expected_ids
            ):
                relevant_result = result
                break


        if relevant_result is None:

            records.append(
                {
                    "question": question,
                    "retrieval_rank": (
                        original_rank
                    ),
                    "reranker_rank": None,
                    "final_rank": None,
                }
            )

            continue


        records.append(
            {
                "question": question,

                "retrieval_rank":
                    relevant_result.retrieval_rank,

                "reranker_rank":
                    relevant_result.reranked_rank,

                "final_rank":
                    relevant_result.final_rank,
            }
        )


    # --------------------------------------------------------
    # Classify final movement relative to original Hybrid
    # --------------------------------------------------------

    improved = []
    worsened = []
    unchanged = []

    top5_rescues = []
    top5_losses = []


    for item in records:

        before = item[
            "retrieval_rank"
        ]

        after = item[
            "final_rank"
        ]

        if before is None:
            continue

        if after is None:

            worsened.append(item)

            if before <= FINAL_K:
                top5_losses.append(item)

            continue


        if after < before:

            improved.append(item)

            if (
                before > FINAL_K
                and after <= FINAL_K
            ):
                top5_rescues.append(
                    item
                )

        elif after > before:

            worsened.append(item)

            if (
                before <= FINAL_K
                and after > FINAL_K
            ):
                top5_losses.append(
                    item
                )

        else:

            unchanged.append(item)


    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    improved.sort(
        key=lambda item: (
            item["retrieval_rank"]
            - item["final_rank"]
        ),
        reverse=True,
    )

    worsened.sort(
        key=lambda item: (
            999
            if item["final_rank"] is None
            else (
                item["final_rank"]
                - item["retrieval_rank"]
            )
        ),
        reverse=True,
    )


    # --------------------------------------------------------
    # Print full movement table
    # --------------------------------------------------------

    print("\n")
    print(
        f"{'Hybrid':>8}"
        f"{'CE':>8}"
        f"{'Final':>8}"
        f"   Question"
    )

    print("-" * 110)

    for item in records:

        hybrid_rank = (
            item["retrieval_rank"]
        )

        ce_rank = (
            item["reranker_rank"]
        )

        final_rank = (
            item["final_rank"]
        )

        print(
            f"{str(hybrid_rank):>8}"
            f"{str(ce_rank):>8}"
            f"{str(final_rank):>8}"
            f"   {item['question']}"
        )


    # --------------------------------------------------------
    # Improved
    # --------------------------------------------------------

    print("\n")
    print("IMPROVED FINAL RANKING")
    print("-" * 110)

    if not improved:

        print("None")

    else:

        for item in improved:

            print(
                f"{item['retrieval_rank']}"
                f" → {item['reranker_rank']}"
                f" → {item['final_rank']}"
                f" | {item['question']}"
            )


    # --------------------------------------------------------
    # Worsened
    # --------------------------------------------------------

    print("\n")
    print("WORSENED FINAL RANKING")
    print("-" * 110)

    if not worsened:

        print("None")

    else:

        for item in worsened:

            print(
                f"{item['retrieval_rank']}"
                f" → {item['reranker_rank']}"
                f" → {item['final_rank']}"
                f" | {item['question']}"
            )


    # --------------------------------------------------------
    # Unchanged
    # --------------------------------------------------------

    print("\n")
    print("UNCHANGED FINAL RANK")
    print("-" * 110)

    print(
        f"{len(unchanged)} questions"
    )


    # --------------------------------------------------------
    # Top-5 Rescues
    # --------------------------------------------------------

    print("\n")
    print("TOP-5 RESCUES")
    print("-" * 110)

    if not top5_rescues:

        print("None")

    else:

        for item in top5_rescues:

            print(
                f"{item['retrieval_rank']}"
                f" → {item['reranker_rank']}"
                f" → {item['final_rank']}"
                f" | {item['question']}"
            )


    # --------------------------------------------------------
    # Top-5 Losses
    # --------------------------------------------------------

    print("\n")
    print("PUSHED OUT OF TOP-5")
    print("-" * 110)

    if not top5_losses:

        print("None")

    else:

        for item in top5_losses:

            print(
                f"{item['retrieval_rank']}"
                f" → {item['reranker_rank']}"
                f" → {item['final_rank']}"
                f" | {item['question']}"
            )


# ============================================================
# LATENCY
# ============================================================

def print_two_stage_latency(
    name,
    retriever,
):

    print("\n" + "=" * 80)
    print(
        f"{name} LATENCY BREAKDOWN"
    )
    print("=" * 80)

    print(
        "Candidate retrieval avg: "
        f"{retriever.average_retrieval_latency_ms():.2f} ms"
    )

    print(
        "Reranking avg: "
        f"{retriever.average_reranker_latency_ms():.2f} ms"
    )

    print(
        "Total avg: "
        f"{retriever.average_total_latency_ms():.2f} ms"
    )


# ============================================================
# FINAL COMPARISON TABLE
# ============================================================

def print_final_comparison(
    dense_results,
    bm25_results,
    hybrid_results,
    dense_ce_results,
    hybrid_ce_results,
    hybrid_fusion_results,
    dense_timed,
    bm25_timed,
    hybrid_timed,
    dense_ce,
    hybrid_ce,
    hybrid_rank_fusion,
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
            "Dense + CE",
            dense_ce_results,
            dense_ce.average_total_latency_ms(),
        ),
        (
            "Hybrid + CE",
            hybrid_ce_results,
            hybrid_ce.average_total_latency_ms(),
        ),
        (
            "Hybrid + CE Rank Fusion",
            hybrid_fusion_results,
            hybrid_rank_fusion.average_total_latency_ms(),
        ),
    ]


    print("\n\n")

    print("=" * 110)

    print(
        "FINAL RETRIEVAL ARCHITECTURE COMPARISON"
    )

    print("=" * 110)


    print(
        f"{'Architecture':<28}"
        f"{'Hit@5':>10}"
        f"{'Recall@5':>12}"
        f"{'Precision@5':>15}"
        f"{'MRR@5':>10}"
        f"{'Latency ms':>15}"
    )

    print("-" * 110)


    for name, result, latency in rows:

        print(
            f"{name:<28}"
            f"{result['hit_rate']:>10.2f}"
            f"{result['recall_rate']:>12.2f}"
            f"{result['avg_precision']:>15.2f}"
            f"{result['mrr_score']:>10.2f}"
            f"{latency:>15.2f}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Dataset
    # --------------------------------------------------------

    dataset = load_evaluation_dataset(
        DATASET_PATH
    )


    # --------------------------------------------------------
    # Dense
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

    fusion = ReciprocalRankFusion(
        k=60
    )

    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        fusion=fusion,
        candidate_k=CANDIDATE_K,
    )


    # --------------------------------------------------------
    # Cross Encoder
    # --------------------------------------------------------

    print("\nLoading cross-encoder...")

    cross_encoder = CrossEncoder(
        RERANKER_MODEL
    )


    # --------------------------------------------------------
    # Pure CE Reranker
    # --------------------------------------------------------

    ce_reranker = CrossEncoderReranker(
        cross_encoder
    )


    # --------------------------------------------------------
    # Rank Fusion Reranker
    # --------------------------------------------------------

    rank_fusion_reranker = (
        RankFusionReranker(
            reranker=ce_reranker,

            retrieval_weight=(
                RETRIEVAL_WEIGHT
            ),

            reranker_weight=(
                RERANKER_WEIGHT
            ),

            rrf_k=RANK_FUSION_K,
        )
    )


    # --------------------------------------------------------
    # Warm Up Model
    # --------------------------------------------------------

    cross_encoder.predict(
        [
            (
                "warmup query",
                "warmup technical document",
            )
        ]
    )


    # ========================================================
    # Candidate Recall
    # ========================================================

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


    # ========================================================
    # Timed Baselines
    # ========================================================

    dense_timed = TimedRetriever(
        dense_retriever
    )

    bm25_timed = TimedRetriever(
        bm25_retriever
    )

    hybrid_timed = TimedRetriever(
        hybrid_retriever
    )


    # ========================================================
    # Two-stage architectures
    # ========================================================

    dense_ce = TwoStageRetriever(
        retriever=dense_retriever,
        reranking_strategy=ce_reranker,
        candidate_k=CANDIDATE_K,
    )

    hybrid_ce = TwoStageRetriever(
        retriever=hybrid_retriever,
        reranking_strategy=ce_reranker,
        candidate_k=CANDIDATE_K,
    )

    hybrid_rank_fusion = TwoStageRetriever(
        retriever=hybrid_retriever,

        reranking_strategy=(
            rank_fusion_reranker
        ),

        candidate_k=CANDIDATE_K,
    )


    # ========================================================
    # Baseline Evaluation
    # ========================================================

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


    # ========================================================
    # Pure CE Evaluation
    # ========================================================

    dense_ce_results = evaluate_retriever(
        "Dense + Cross-Encoder",
        dense_ce,
        dataset,
        k=FINAL_K,
    )

    hybrid_ce_results = evaluate_retriever(
        "Hybrid + Cross-Encoder",
        hybrid_ce,
        dataset,
        k=FINAL_K,
    )


    # ========================================================
    # Rank-Fusion Evaluation
    # ========================================================

    hybrid_fusion_results = (
        evaluate_retriever(
            (
                "Hybrid + Cross-Encoder "
                "+ Rank Fusion"
            ),
            hybrid_rank_fusion,
            dataset,
            k=FINAL_K,
        )
    )


    # ========================================================
    # Candidate Recall Summary
    # ========================================================

    print("\n\n")
    print("=" * 80)
    print("CANDIDATE RECALL SUMMARY")
    print("=" * 80)

    print(
        f"Dense Recall@{CANDIDATE_K}: "
        f"{dense_candidate_results['recall_rate']:.2f}"
    )

    print(
        f"Hybrid Recall@{CANDIDATE_K}: "
        f"{hybrid_candidate_results['recall_rate']:.2f}"
    )


    # ========================================================
    # Hit Analysis
    # ========================================================

    analyze_hit_changes(
        baseline_name="Hybrid",
        baseline_results=hybrid_results,

        new_name="Hybrid + CE",
        new_results=hybrid_ce_results,
    )

    analyze_hit_changes(
        baseline_name="Hybrid",
        baseline_results=hybrid_results,

        new_name=(
            "Hybrid + CE Rank Fusion"
        ),
        new_results=hybrid_fusion_results,
    )

    analyze_hit_changes(
        baseline_name="Hybrid + CE",
        baseline_results=hybrid_ce_results,

        new_name=(
            "Hybrid + CE Rank Fusion"
        ),
        new_results=hybrid_fusion_results,
    )


    # ========================================================
    # Latency
    # ========================================================

    print_two_stage_latency(
        "DENSE + CE",
        dense_ce,
    )

    print_two_stage_latency(
        "HYBRID + CE",
        hybrid_ce,
    )

    print_two_stage_latency(
        "HYBRID + CE RANK FUSION",
        hybrid_rank_fusion,
    )


    # ========================================================
    # Final Comparison
    # ========================================================

    print_final_comparison(
        dense_results=dense_results,
        bm25_results=bm25_results,
        hybrid_results=hybrid_results,

        dense_ce_results=dense_ce_results,
        hybrid_ce_results=hybrid_ce_results,

        hybrid_fusion_results=(
            hybrid_fusion_results
        ),

        dense_timed=dense_timed,
        bm25_timed=bm25_timed,
        hybrid_timed=hybrid_timed,

        dense_ce=dense_ce,
        hybrid_ce=hybrid_ce,

        hybrid_rank_fusion=(
            hybrid_rank_fusion
        ),
    )


    # ========================================================
    # IMPORTANT:
    #
    # Run detailed movement analysis LAST.
    #
    # It performs additional model inference and therefore
    # should not contaminate the latency averages above.
    # ========================================================

    analyze_rank_fusion_movements(
        hybrid_retriever=(
            hybrid_retriever
        ),

        rank_fusion_retriever=(
            hybrid_rank_fusion
        ),

        dataset=dataset,
    )


if __name__ == "__main__":
    main()