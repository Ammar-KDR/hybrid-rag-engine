import csv
import gc
import json
import math
import time
import uuid

from dataclasses import dataclass
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from sentence_transformers import (
    CrossEncoder,
    SentenceTransformer,
)

from rag.retrieval.bm25_retrieval import BM25Retriever
from rag.retrieval.Dense_retrieval import DenseRetriever
from rag.retrieval.hybrid_retreival import HybridRetriever
from rag.retrieval.fusion import ReciprocalRankFusion

from rag.embedding.service import EmbeddingService
from rag.vector_store.qdrant import QdrantVectorStore

from rag.reranking.reranker import CrossEncoderReranker
from rag.reranking.rank_fusion_reranker import RankFusionReranker


# ============================================================
# CONFIGURATION
# ============================================================

SCIFACT_DIR = Path(
    "data/benchmarks/scifact"
)

CORPUS_PATH = (
    SCIFACT_DIR / "corpus.jsonl"
)

QUERIES_PATH = (
    SCIFACT_DIR / "queries.jsonl"
)

QRELS_PATH = (
    SCIFACT_DIR / "qrels" / "test.tsv"
)


# Temporary benchmark collection.
#
# Keep this separate from our project collections.
COLLECTION_NAME = "beir_scifact"


# This must point to the same Qdrant server used by
# QdrantVectorStore.
QDRANT_URL = "http://localhost:6333"


# ------------------------------------------------------------
# Retrieval configuration
# ------------------------------------------------------------

CANDIDATE_K = 20

EVALUATION_K = 10

RECALL_K = 20


# ------------------------------------------------------------
# Dense embedding model
# ------------------------------------------------------------

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

EMBEDDING_DIMENSION = 384


# ------------------------------------------------------------
# Reranker
# ------------------------------------------------------------

RERANKER_MODEL = (
    "BAAI/bge-reranker-base"
)


# ------------------------------------------------------------
# Existing Hybrid RRF
# ------------------------------------------------------------

HYBRID_RRF_K = 60


# ------------------------------------------------------------
# Hybrid-aware CE rank fusion
#
# Keep these frozen.
# ------------------------------------------------------------

RETRIEVAL_WEIGHT = 0.5
RERANKER_WEIGHT = 0.5
RANK_FUSION_K = 60


# ------------------------------------------------------------
# Indexing
# ------------------------------------------------------------

INDEX_BATCH_SIZE = 64


# True:
#     delete/rebuild SciFact Qdrant collection
#
# False:
#     reuse it if all corpus documents are already indexed
REBUILD_INDEX = False


# ------------------------------------------------------------
# Development option
#
# Leave None for the real benchmark.
#
# You can temporarily use:
#
# QUERY_LIMIT = 25
#
# just to verify the pipeline works.
# ------------------------------------------------------------

QUERY_LIMIT = None


# ============================================================
# BENCHMARK CHUNK
# ============================================================

@dataclass
class BenchmarkChunk:
    """
    SciFact document adapted to the same interface expected
    by our project's BM25Retriever.

    Important:
    chunk_id remains the original BEIR corpus document ID
    so it matches qrels exactly.
    """

    chunk_id: str
    text: str
    source: str
    file_type: str
    chunk_index: int
    chunking_strategy: str
    metadata: dict


# ============================================================
# LOAD JSONL
# ============================================================

def load_jsonl(path: Path):

    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    items = []

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            items.append(
                json.loads(line)
            )

    return items


# ============================================================
# LOAD SCIFACT CORPUS
# ============================================================

def load_scifact_corpus():

    raw_documents = load_jsonl(
        CORPUS_PATH
    )

    corpus = {}

    chunks = []

    for chunk_index, document in enumerate(raw_documents):

        doc_id = str(
            document["_id"]
        )

        title = (
            document.get("title")
            or ""
        ).strip()

        body = (
            document.get("text")
            or ""
        ).strip()

        # ----------------------------------------------------
        # Dense/BM25 both see title + abstract.
        # ----------------------------------------------------

        if title and body:

            retrieval_text = (
                f"{title}\n\n{body}"
            )

        elif title:

            retrieval_text = title

        else:

            retrieval_text = body


        corpus[doc_id] = {
            "title": title,
            "text": body,
            "retrieval_text": retrieval_text,
        }


        chunks.append(
    BenchmarkChunk(
        chunk_id=doc_id,
        text=retrieval_text,

        source="BEIR/SciFact",
        file_type="scifact",

        chunk_index=len(chunks),

        chunking_strategy="document",

        metadata={
            "beir_doc_id": doc_id,
            "title": title,
        },
    )
)

    return corpus, chunks


# ============================================================
# LOAD QUERIES
# ============================================================

def load_scifact_queries():

    raw_queries = load_jsonl(
        QUERIES_PATH
    )

    queries = {}

    for item in raw_queries:

        query_id = str(
            item["_id"]
        )

        queries[query_id] = (
            item["text"].strip()
        )

    return queries


# ============================================================
# LOAD QRELS
# ============================================================

def load_scifact_qrels():

    if not QRELS_PATH.exists():

        raise FileNotFoundError(
            f"Missing file: {QRELS_PATH}"
        )

    qrels = {}

    with open(
        QRELS_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(
            file,
            delimiter="\t",
        )

        for row in reader:

            # BEIR commonly uses:
            #
            # query-id
            # corpus-id
            # score

            query_id = str(
                row.get("query-id")
                or row.get("query_id")
            )

            corpus_id = str(
                row.get("corpus-id")
                or row.get("corpus_id")
            )

            score = int(
                row["score"]
            )

            if query_id not in qrels:
                qrels[query_id] = {}

            qrels[query_id][
                corpus_id
            ] = score

    return qrels


# ============================================================
# VALIDATE BENCHMARK
# ============================================================

def validate_benchmark(
    corpus,
    queries,
    qrels,
):

    missing_queries = []

    missing_documents = []

    for query_id, relevant_docs in qrels.items():

        if query_id not in queries:

            missing_queries.append(
                query_id
            )

        for doc_id in relevant_docs:

            if doc_id not in corpus:

                missing_documents.append(
                    (
                        query_id,
                        doc_id,
                    )
                )

    print("\n" + "=" * 80)
    print("SCIFACT INTEGRITY CHECK")
    print("=" * 80)

    print(
        f"Corpus documents: {len(corpus)}"
    )

    print(
        f"Queries loaded: {len(queries)}"
    )

    print(
        f"Judged test queries: {len(qrels)}"
    )

    print(
        f"Missing judged queries: "
        f"{len(missing_queries)}"
    )

    print(
        f"Missing relevant documents: "
        f"{len(missing_documents)}"
    )

    if (
        missing_queries
        or missing_documents
    ):

        print("\nFAIL")

        if missing_queries:

            print(
                "\nMissing query IDs:"
            )

            for query_id in missing_queries:

                print(
                    f"- {query_id}"
                )

        if missing_documents:

            print(
                "\nMissing corpus IDs:"
            )

            for (
                query_id,
                doc_id,
            ) in missing_documents:

                print(
                    f"- query={query_id}, "
                    f"doc={doc_id}"
                )

        raise RuntimeError(
            "SciFact integrity validation failed."
        )

    print("\nPASS")


# ============================================================
# STABLE QDRANT POINT ID
# ============================================================

def qdrant_point_id(
    beir_doc_id: str,
):

    """
    Qdrant point IDs can use UUIDs.

    Our application-level identity remains the original
    BEIR document ID stored in payload['chunk_id'].
    """

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"beir-scifact:{beir_doc_id}",
        )
    )


# ============================================================
# BUILD / REUSE QDRANT INDEX
# ============================================================

def prepare_qdrant_index(
    chunks,
):

    client = QdrantClient(
        url=QDRANT_URL
    )

    collection_exists = (
        client.collection_exists(
            COLLECTION_NAME
        )
    )


    # --------------------------------------------------------
    # Reuse existing complete index
    # --------------------------------------------------------

    if (
        collection_exists
        and not REBUILD_INDEX
    ):

        indexed_count = (
            client.count(
                collection_name=(
                    COLLECTION_NAME
                ),
                exact=True,
            ).count
        )

        if indexed_count == len(chunks):

            print(
                "\nSciFact Qdrant collection "
                "already exists."
            )

            print(
                f"Indexed documents: "
                f"{indexed_count}"
            )

            print(
                "Skipping corpus embedding."
            )

            return


    # --------------------------------------------------------
    # Rebuild
    # --------------------------------------------------------

    if collection_exists:

        print(
            "\nDeleting existing SciFact "
            "benchmark collection..."
        )

        client.delete_collection(
            collection_name=(
                COLLECTION_NAME
            )
        )


    print(
        "\nCreating SciFact "
        "benchmark collection..."
    )

    client.create_collection(
        collection_name=COLLECTION_NAME,

        vectors_config=VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=Distance.COSINE,
        ),
    )


    # --------------------------------------------------------
    # Load embedding model for corpus indexing
    # --------------------------------------------------------

    print(
        "\nLoading corpus embedding model..."
    )

    encoder = SentenceTransformer(
        EMBEDDING_MODEL
    )


    print(
        f"\nEmbedding/indexing "
        f"{len(chunks)} SciFact documents..."
    )


    # --------------------------------------------------------
    # Batch indexing
    # --------------------------------------------------------

    total = len(chunks)

    for start in range(
        0,
        total,
        INDEX_BATCH_SIZE,
    ):

        end = min(
            start + INDEX_BATCH_SIZE,
            total,
        )

        batch = chunks[
            start:end
        ]

        texts = [
            chunk.text
            for chunk in batch
        ]


        embeddings = encoder.encode(
            texts,

            batch_size=INDEX_BATCH_SIZE,

            normalize_embeddings=True,

            show_progress_bar=False,
        )


        points = []

        for chunk, embedding in zip(
            batch,
            embeddings,
        ):

            points.append(
                PointStruct(
                    id=qdrant_point_id(
                        chunk.chunk_id
                    ),

                    vector=(
                        embedding.tolist()
                    ),

                    payload={
                        "chunk_id":
                            chunk.chunk_id,

                        "text":
                            chunk.text,

                        "metadata":
                            chunk.metadata,
                    },
                )
            )


        client.upsert(
            collection_name=(
                COLLECTION_NAME
            ),
            points=points,
        )


        print(
            f"Indexed "
            f"{end:>4}/{total}"
        )


    final_count = (
        client.count(
            collection_name=(
                COLLECTION_NAME
            ),
            exact=True,
        ).count
    )


    print(
        "\nIndex complete."
    )

    print(
        f"Qdrant document count: "
        f"{final_count}"
    )


    if final_count != total:

        raise RuntimeError(
            "Qdrant indexing count does not "
            "match SciFact corpus size."
        )


    # Release the temporary indexing model.
    #
    # DenseRetriever will use our project's
    # EmbeddingService for queries.
    del encoder

    gc.collect()


# ============================================================
# GENERIC TWO-STAGE RETRIEVER
# ============================================================

class TwoStageRetriever:

    def __init__(
        self,
        retriever,
        reranking_strategy,
        candidate_k=20,
    ):

        self.retriever = retriever

        self.reranking_strategy = (
            reranking_strategy
        )

        self.candidate_k = candidate_k


    def retrieve(
        self,
        query: str,
        top_k: int = 10,
    ):

        candidates = (
            self.retriever.retrieve(
                query=query,
                top_k=self.candidate_k,
            )
        )

        return (
            self.reranking_strategy.rerank(
                query=query,
                candidates=candidates,
                top_k=top_k,
            )
        )


# ============================================================
# METRIC HELPERS
# ============================================================

def relevant_documents(
    qrel_for_query,
):

    return {
        doc_id
        for doc_id, relevance
        in qrel_for_query.items()
        if relevance > 0
    }


def precision_at_k(
    ranked_doc_ids,
    qrel_for_query,
    k,
):

    relevant = relevant_documents(
        qrel_for_query
    )

    top_k = ranked_doc_ids[:k]

    hits = sum(
        doc_id in relevant
        for doc_id in top_k
    )

    return hits / k


def recall_at_k(
    ranked_doc_ids,
    qrel_for_query,
    k,
):

    relevant = relevant_documents(
        qrel_for_query
    )

    if not relevant:
        return 0.0

    hits = sum(
        doc_id in relevant
        for doc_id
        in ranked_doc_ids[:k]
    )

    return (
        hits
        / len(relevant)
    )


def reciprocal_rank_at_k(
    ranked_doc_ids,
    qrel_for_query,
    k,
):

    relevant = relevant_documents(
        qrel_for_query
    )

    for rank, doc_id in enumerate(
        ranked_doc_ids[:k],
        start=1,
    ):

        if doc_id in relevant:

            return 1.0 / rank

    return 0.0


def average_precision_at_k(
    ranked_doc_ids,
    qrel_for_query,
    k,
):

    relevant = relevant_documents(
        qrel_for_query
    )

    if not relevant:
        return 0.0

    hits = 0

    precision_sum = 0.0

    for rank, doc_id in enumerate(
        ranked_doc_ids[:k],
        start=1,
    ):

        if doc_id in relevant:

            hits += 1

            precision_sum += (
                hits / rank
            )


    denominator = min(
        len(relevant),
        k,
    )

    return (
        precision_sum
        / denominator
    )


def dcg_at_k(
    ranked_doc_ids,
    qrel_for_query,
    k,
):

    score = 0.0

    for rank, doc_id in enumerate(
        ranked_doc_ids[:k],
        start=1,
    ):

        relevance = (
            qrel_for_query.get(
                doc_id,
                0,
            )
        )

        gain = (
            (2 ** relevance)
            - 1
        )

        discount = math.log2(
            rank + 1
        )

        score += (
            gain
            / discount
        )

    return score


def ndcg_at_k(
    ranked_doc_ids,
    qrel_for_query,
    k,
):

    actual_dcg = dcg_at_k(
        ranked_doc_ids,
        qrel_for_query,
        k,
    )


    ideal_relevances = sorted(
        qrel_for_query.values(),
        reverse=True,
    )[:k]


    ideal_dcg = 0.0

    for rank, relevance in enumerate(
        ideal_relevances,
        start=1,
    ):

        gain = (
            (2 ** relevance)
            - 1
        )

        discount = math.log2(
            rank + 1
        )

        ideal_dcg += (
            gain
            / discount
        )


    if ideal_dcg == 0:
        return 0.0

    return (
        actual_dcg
        / ideal_dcg
    )


# ============================================================
# EVALUATE ONE ARCHITECTURE
# ============================================================

def evaluate_architecture(
    name,
    retriever,
    queries,
    qrels,
):

    print("\n")
    print("=" * 80)
    print(f"EVALUATING: {name}")
    print("=" * 80)


    query_ids = list(
        qrels.keys()
    )


    if QUERY_LIMIT is not None:

        query_ids = query_ids[
            :QUERY_LIMIT
        ]


    ndcg_scores = []

    map_scores = []

    recall_10_scores = []

    recall_20_scores = []

    precision_scores = []

    mrr_scores = []

    latencies = []


    # Useful for later failure inspection.
    per_query = []


    total_queries = len(
        query_ids
    )


    for index, query_id in enumerate(
        query_ids,
        start=1,
    ):

        query = queries[
            query_id
        ]


        # ----------------------------------------------------
        # Retrieve enough results for Recall@20.
        # ----------------------------------------------------

        start = time.perf_counter()

        results = retriever.retrieve(
            query=query,
            top_k=RECALL_K,
        )

        latency_ms = (
            time.perf_counter()
            - start
        ) * 1000


        latencies.append(
            latency_ms
        )


        # ----------------------------------------------------
        # Preserve unique document order
        # ----------------------------------------------------

        ranked_doc_ids = []

        seen = set()

        for result in results:

            doc_id = str(
                result.chunk_id
            )

            if doc_id in seen:
                continue

            seen.add(doc_id)

            ranked_doc_ids.append(
                doc_id
            )


        qrel = qrels[
            query_id
        ]


        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        ndcg = ndcg_at_k(
            ranked_doc_ids,
            qrel,
            EVALUATION_K,
        )

        ap = average_precision_at_k(
            ranked_doc_ids,
            qrel,
            EVALUATION_K,
        )

        recall_10 = recall_at_k(
            ranked_doc_ids,
            qrel,
            EVALUATION_K,
        )

        recall_20 = recall_at_k(
            ranked_doc_ids,
            qrel,
            RECALL_K,
        )

        precision = precision_at_k(
            ranked_doc_ids,
            qrel,
            EVALUATION_K,
        )

        mrr = reciprocal_rank_at_k(
            ranked_doc_ids,
            qrel,
            EVALUATION_K,
        )


        ndcg_scores.append(
            ndcg
        )

        map_scores.append(
            ap
        )

        recall_10_scores.append(
            recall_10
        )

        recall_20_scores.append(
            recall_20
        )

        precision_scores.append(
            precision
        )

        mrr_scores.append(
            mrr
        )


        per_query.append(
            {
                "query_id":
                    query_id,

                "query":
                    query,

                "ranked_doc_ids":
                    ranked_doc_ids,

                "NDCG@10":
                    ndcg,

                "MAP@10":
                    ap,

                "Recall@10":
                    recall_10,

                "Recall@20":
                    recall_20,

                "P@10":
                    precision,

                "MRR@10":
                    mrr,

                "latency_ms":
                    latency_ms,
            }
        )


        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            index % 25 == 0
            or index == total_queries
        ):

            print(
                f"{index}/{total_queries} "
                f"queries complete"
            )


    # --------------------------------------------------------
    # Aggregate
    # --------------------------------------------------------

    count = len(
        query_ids
    )


    metrics = {
        "NDCG@10":
            sum(ndcg_scores)
            / count,

        "MAP@10":
            sum(map_scores)
            / count,

        "Recall@10":
            sum(recall_10_scores)
            / count,

        "Recall@20":
            sum(recall_20_scores)
            / count,

        "P@10":
            sum(precision_scores)
            / count,

        "MRR@10":
            sum(mrr_scores)
            / count,

        "LatencyMs":
            sum(latencies)
            / count,

        "per_query":
            per_query,
    }


    print("\nResults")

    print(
        f"NDCG@10:   "
        f"{metrics['NDCG@10']:.4f}"
    )

    print(
        f"MAP@10:    "
        f"{metrics['MAP@10']:.4f}"
    )

    print(
        f"Recall@10: "
        f"{metrics['Recall@10']:.4f}"
    )

    print(
        f"Recall@20: "
        f"{metrics['Recall@20']:.4f}"
    )

    print(
        f"P@10:      "
        f"{metrics['P@10']:.4f}"
    )

    print(
        f"MRR@10:    "
        f"{metrics['MRR@10']:.4f}"
    )

    print(
        f"Latency:   "
        f"{metrics['LatencyMs']:.2f} ms"
    )


    return metrics


# ============================================================
# PRINT FINAL TABLE
# ============================================================

def print_comparison_table(
    all_results,
):

    print("\n\n")

    print("=" * 125)

    print(
        "BEIR SCIFACT — "
        "RETRIEVAL ARCHITECTURE COMPARISON"
    )

    print("=" * 125)


    print(
        f"{'Architecture':<32}"
        f"{'NDCG@10':>12}"
        f"{'MAP@10':>12}"
        f"{'Recall@10':>14}"
        f"{'Recall@20':>14}"
        f"{'P@10':>10}"
        f"{'MRR@10':>12}"
        f"{'Latency':>14}"
    )

    print("-" * 125)


    for name, metrics in all_results:

        print(
            f"{name:<32}"

            f"{metrics['NDCG@10']:>12.4f}"

            f"{metrics['MAP@10']:>12.4f}"

            f"{metrics['Recall@10']:>14.4f}"

            f"{metrics['Recall@20']:>14.4f}"

            f"{metrics['P@10']:>10.4f}"

            f"{metrics['MRR@10']:>12.4f}"

            f"{metrics['LatencyMs']:>11.2f} ms"
        )


# ============================================================
# FAILURE COMPARISON
# ============================================================

def compare_hybrid_vs_fusion(
    hybrid_metrics,
    fusion_metrics,
):

    print("\n\n")

    print("=" * 100)

    print(
        "QUERY-LEVEL ANALYSIS: "
        "HYBRID → BGE + RANK FUSION"
    )

    print("=" * 100)


    hybrid_items = {
        item["query_id"]: item
        for item
        in hybrid_metrics["per_query"]
    }

    fusion_items = {
        item["query_id"]: item
        for item
        in fusion_metrics["per_query"]
    }


    improvements = []

    regressions = []


    for query_id in hybrid_items:

        before = hybrid_items[
            query_id
        ]

        after = fusion_items[
            query_id
        ]


        delta = (
            after["NDCG@10"]
            - before["NDCG@10"]
        )


        record = {
            "query_id":
                query_id,

            "query":
                before["query"],

            "before":
                before["NDCG@10"],

            "after":
                after["NDCG@10"],

            "delta":
                delta,
        }


        if delta > 0:

            improvements.append(
                record
            )

        elif delta < 0:

            regressions.append(
                record
            )


    improvements.sort(
        key=lambda item:
            item["delta"],
        reverse=True,
    )

    regressions.sort(
        key=lambda item:
            item["delta"],
    )


    print(
        f"\nQueries improved: "
        f"{len(improvements)}"
    )

    print(
        f"Queries worsened: "
        f"{len(regressions)}"
    )


    print("\n")
    print("TOP 10 IMPROVEMENTS")
    print("-" * 100)

    for item in improvements[:10]:

        print(
            f"{item['before']:.3f}"
            f" → "
            f"{item['after']:.3f}"
            f" | "
            f"{item['query']}"
        )


    print("\n")
    print("TOP 10 REGRESSIONS")
    print("-" * 100)

    for item in regressions[:10]:

        print(
            f"{item['before']:.3f}"
            f" → "
            f"{item['after']:.3f}"
            f" | "
            f"{item['query']}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load benchmark
    # --------------------------------------------------------

    print(
        "\nLoading SciFact..."
    )


    corpus, chunks = (
        load_scifact_corpus()
    )


    queries = (
        load_scifact_queries()
    )


    qrels = (
        load_scifact_qrels()
    )


    # --------------------------------------------------------
    # Validate benchmark integrity
    # --------------------------------------------------------

    validate_benchmark(
        corpus=corpus,
        queries=queries,
        qrels=qrels,
    )


    # --------------------------------------------------------
    # Prepare Qdrant benchmark collection
    # --------------------------------------------------------

    prepare_qdrant_index(
        chunks
    )


    # ========================================================
    # BUILD OUR RETRIEVAL STACK
    # ========================================================


    # --------------------------------------------------------
    # Dense
    # --------------------------------------------------------

    print(
        "\nLoading DenseRetriever..."
    )


    embedding_service = (
        EmbeddingService()
    )


    vector_store = (
        QdrantVectorStore()
    )


    dense_retriever = (
        DenseRetriever(
            embedding_service=(
                embedding_service
            ),

            vector_store=(
                vector_store
            ),

            collection_name=(
                COLLECTION_NAME
            ),
        )
    )


    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    print(
        "\nBuilding BM25 index..."
    )


    bm25_retriever = (
        BM25Retriever(
            chunks
        )
    )


    # --------------------------------------------------------
    # Hybrid
    # --------------------------------------------------------

    hybrid_rrf = (
        ReciprocalRankFusion(
            k=HYBRID_RRF_K
        )
    )


    hybrid_retriever = (
        HybridRetriever(
            dense_retriever=(
                dense_retriever
            ),

            bm25_retriever=(
                bm25_retriever
            ),

            fusion=(
                hybrid_rrf
            ),

            candidate_k=(
                CANDIDATE_K
            ),
        )
    )


    # ========================================================
    # LOAD BGE RERANKER
    # ========================================================

    print(
        "\nLoading BGE reranker..."
    )


    cross_encoder = (
        CrossEncoder(
            RERANKER_MODEL
        )
    )


    ce_reranker = (
        CrossEncoderReranker(
            cross_encoder
        )
    )


    # --------------------------------------------------------
    # Hybrid-aware Rank Fusion
    # --------------------------------------------------------

    rank_fusion_reranker = (
        RankFusionReranker(
            reranker=(
                ce_reranker
            ),

            retrieval_weight=(
                RETRIEVAL_WEIGHT
            ),

            reranker_weight=(
                RERANKER_WEIGHT
            ),

            rrf_k=(
                RANK_FUSION_K
            ),
        )
    )


    # --------------------------------------------------------
    # Warm up BGE
    # --------------------------------------------------------

    print(
        "\nWarming up BGE..."
    )


    cross_encoder.predict(
        [
            (
                "scientific query",
                "scientific document",
            )
        ]
    )


    # ========================================================
    # TWO-STAGE ARCHITECTURES
    # ========================================================

    hybrid_bge = (
        TwoStageRetriever(
            retriever=(
                hybrid_retriever
            ),

            reranking_strategy=(
                ce_reranker
            ),

            candidate_k=(
                CANDIDATE_K
            ),
        )
    )


    hybrid_bge_fusion = (
        TwoStageRetriever(
            retriever=(
                hybrid_retriever
            ),

            reranking_strategy=(
                rank_fusion_reranker
            ),

            candidate_k=(
                CANDIDATE_K
            ),
        )
    )


    # ========================================================
    # RUN BENCHMARK
    # ========================================================

    results = []


    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    bm25_metrics = (
        evaluate_architecture(
            name="BM25",
            retriever=(
                bm25_retriever
            ),
            queries=queries,
            qrels=qrels,
        )
    )

    results.append(
        (
            "BM25",
            bm25_metrics,
        )
    )


    # --------------------------------------------------------
    # Dense
    # --------------------------------------------------------

    dense_metrics = (
        evaluate_architecture(
            name="Dense",
            retriever=(
                dense_retriever
            ),
            queries=queries,
            qrels=qrels,
        )
    )

    results.append(
        (
            "Dense",
            dense_metrics,
        )
    )


    # --------------------------------------------------------
    # Hybrid
    # --------------------------------------------------------

    hybrid_metrics = (
        evaluate_architecture(
            name="Hybrid",
            retriever=(
                hybrid_retriever
            ),
            queries=queries,
            qrels=qrels,
        )
    )

    results.append(
        (
            "Hybrid",
            hybrid_metrics,
        )
    )


    # --------------------------------------------------------
    # Hybrid + pure BGE
    # --------------------------------------------------------

    hybrid_bge_metrics = (
        evaluate_architecture(
            name="Hybrid + BGE",
            retriever=(
                hybrid_bge
            ),
            queries=queries,
            qrels=qrels,
        )
    )

    results.append(
        (
            "Hybrid + BGE",
            hybrid_bge_metrics,
        )
    )


    # --------------------------------------------------------
    # Hybrid + BGE + retrieval-aware rank fusion
    # --------------------------------------------------------

    hybrid_bge_fusion_metrics = (
        evaluate_architecture(
            name=(
                "Hybrid + BGE + Rank Fusion"
            ),

            retriever=(
                hybrid_bge_fusion
            ),

            queries=queries,
            qrels=qrels,
        )
    )

    results.append(
        (
            "Hybrid + BGE + Rank Fusion",
            hybrid_bge_fusion_metrics,
        )
    )


    # ========================================================
    # FINAL TABLE
    # ========================================================

    print_comparison_table(
        results
    )


    # ========================================================
    # FAILURE / IMPROVEMENT ANALYSIS
    # ========================================================

    compare_hybrid_vs_fusion(
        hybrid_metrics=(
            hybrid_metrics
        ),

        fusion_metrics=(
            hybrid_bge_fusion_metrics
        ),
    )


if __name__ == "__main__":
    main()