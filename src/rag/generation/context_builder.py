import unicodedata
from .model import ContextBlock, BuiltContext
from rag.reranking.model import RerankedChunk


class ContextBuilder:
    """
    Constructs grounded context for the generation stage.
    
    Filters retrieved / reranked candidate chunks using dynamic thresholding:
    - Never exceeds `final_context_k`.
    - Eliminates low-scoring noise chunks below `min_score_threshold`.
    - If the top candidate is confident, filters out distant low-relevance
      candidates whose score is below `relative_threshold_ratio * top_score`.
    - Preserves at least 1 candidate (the top candidate) when chunks are provided.
    """

    def __init__(
        self,
        final_context_k: int = 5,
        min_score_threshold: float = 0.01,
        relative_threshold_ratio: float = 0.08,
    ):
        if final_context_k <= 0:
            raise ValueError(
                "final_context_k must be greater than 0"
            )
        if relative_threshold_ratio < 0:
            raise ValueError(
                "relative_threshold_ratio must be >= 0"
            )

        self.final_context_k = final_context_k
        self.min_score_threshold = min_score_threshold
        self.relative_threshold_ratio = relative_threshold_ratio

    def filter_chunks(
        self,
        chunks: list[RerankedChunk],
    ) -> list[RerankedChunk]:
        if not chunks:
            return []

        candidates = chunks[: self.final_context_k]
        if len(candidates) <= 1:
            return candidates

        top_score = self._get_chunk_score(candidates[0])
        if top_score is None:
            return candidates

        filtered = [candidates[0]]

        for chunk in candidates[1:]:
            score = self._get_chunk_score(chunk)
            if score is None:
                filtered.append(chunk)
                continue

            # Absolute threshold: reject pure noise (< min_score_threshold)
            if score < self.min_score_threshold:
                continue

            # Relative threshold: if top candidate has high/moderate relevance,
            # reject chunks that are far below the top candidate's score
            if top_score > 0 and score < (top_score * self.relative_threshold_ratio):
                continue

            filtered.append(chunk)

        return filtered

    @staticmethod
    def _get_chunk_score(chunk) -> float | None:
        if hasattr(chunk, "reranker_score") and chunk.reranker_score is not None:
            return float(chunk.reranker_score)
        if hasattr(chunk, "final_score") and chunk.final_score is not None:
            return float(chunk.final_score)
        if hasattr(chunk, "score") and chunk.score is not None:
            return float(chunk.score)
        return None

    def build(
        self,
        chunks: list[RerankedChunk],
    ) -> BuiltContext:

        selected_chunks = self.filter_chunks(chunks)

        blocks = []

        for reference, chunk in enumerate(
            selected_chunks,
            start=1,
        ):
            metadata = chunk.metadata or {}
            normalized_text = unicodedata.normalize("NFKC", chunk.text)

            block = ContextBlock(
                reference=reference,
                chunk_id=chunk.chunk_id,
                text=normalized_text,
                source=metadata.get("source"),
                file_type=metadata.get("file_type"),
                page_number=metadata.get("page_number"),
                heading_path=metadata.get("heading_path"),
                document_id=metadata.get("document_id"),
                filename=metadata.get("filename"),
                final_score=getattr(chunk, "final_score", None),
                reranker_score=getattr(chunk, "reranker_score", None),
            )

            blocks.append(block)

        context_text = self._render_blocks(blocks)

        return BuiltContext(
            text=context_text,
            blocks=blocks,
        )

    def _render_blocks(
        self,
        blocks: list[ContextBlock],
    ) -> str:

        rendered_blocks = []

        for block in blocks:
            lines = [
                f"[{block.reference}]"
            ]

            if block.source:
                lines.append(
                    f"Source: {block.source}"
                )

            if block.page_number is not None:
                lines.append(
                    f"Page: {block.page_number}"
                )

            if block.heading_path:
                lines.append(
                    "Section: "
                    + " > ".join(block.heading_path)
                )

            lines.append("")
            lines.append(block.text.strip())

            lines.append(
                f"[/{block.reference}]"
            )

            rendered_blocks.append(
                "\n".join(lines)
            )

        return "\n\n".join(rendered_blocks)