from dataclasses import replace

from rag.retrieval.model import RetrievedChunk
from .model import RerankedChunk
from .reranker import CrossEncoderReranker


class RankFusionReranker:
    """
    Combines:

        1. Original first-stage retrieval rank
        2. Cross-encoder reranker rank

    using weighted reciprocal-rank fusion.

    The purpose is to allow the cross-encoder to improve semantic
    ranking without completely discarding strong lexical/hybrid
    retrieval signals.

    Input:
        query
        list[RetrievedChunk]

    Output:
        list[RerankedChunk]
    """

    def __init__(
        self,
        reranker: CrossEncoderReranker,
        retrieval_weight: float = 0.5,
        reranker_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        if retrieval_weight < 0:
            raise ValueError(
                "retrieval_weight must be >= 0"
            )

        if reranker_weight < 0:
            raise ValueError(
                "reranker_weight must be >= 0"
            )

        if (
            retrieval_weight == 0
            and reranker_weight == 0
        ):
            raise ValueError(
                "At least one weight must be greater than 0"
            )

        if rrf_k < 0:
            raise ValueError(
                "rrf_k must be >= 0"
            )

        self.reranker = reranker

        self.retrieval_weight = retrieval_weight
        self.reranker_weight = reranker_weight

        self.rrf_k = rrf_k


    def rerank(
        self,
        query: str,
        candidates: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RerankedChunk]:

        # --------------------------------------------------
        # Validation
        # --------------------------------------------------

        if not query.strip():
            raise ValueError(
                "Query cannot be empty"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0"
            )

        if len(candidates) == 0:
            return []


        # --------------------------------------------------
        # Stage 1
        #
        # Run the normal cross-encoder reranker across ALL
        # candidates.
        #
        # We explicitly request len(candidates), because the
        # fusion stage needs every candidate's CE rank.
        # --------------------------------------------------

        ce_results = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=len(candidates),
        )


        # --------------------------------------------------
        # Stage 2
        #
        # Combine original retrieval rank with CE rank.
        #
        # final_score =
        #
        # retrieval_weight / (k + retrieval_rank)
        # +
        # reranker_weight / (k + reranker_rank)
        #
        # We use ranks rather than raw scores because:
        #
        # - Hybrid/RRF scores have one scale
        # - Dense scores have another
        # - Cross-encoder logits have another
        #
        # Rank fusion avoids score-calibration problems.
        # --------------------------------------------------

        fused_results = []

        for result in ce_results:

            retrieval_component = (
                self.retrieval_weight
                / (
                    self.rrf_k
                    + result.retrieval_rank
                )
            )

            reranker_component = (
                self.reranker_weight
                / (
                    self.rrf_k
                    + result.reranked_rank
                )
            )

            final_score = (
                retrieval_component
                + reranker_component
            )

            fused_results.append(
                (
                    result,
                    final_score,
                )
            )


        # --------------------------------------------------
        # Stage 3
        #
        # Highest fused score wins.
        # --------------------------------------------------

        fused_results.sort(
            key=lambda item: item[1],
            reverse=True,
        )


        # --------------------------------------------------
        # Stage 4
        #
        # Assign final ranks while preserving:
        #
        # retrieval rank
        # retrieval score
        # reranker rank
        # reranker score
        # --------------------------------------------------

        final_results = []

        for final_rank, (
            result,
            final_score,
        ) in enumerate(
            fused_results,
            start=1,
        ):

            final_result = replace(
                result,
                final_score=float(final_score),
                final_rank=final_rank,
            )

            final_results.append(
                final_result
            )


        # --------------------------------------------------
        # Stage 5
        #
        # Return only requested final results.
        # --------------------------------------------------

        return final_results[:top_k]