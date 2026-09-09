from .model import ContextBlock, BuiltContext
from rag.reranking.model import RerankedChunk




class ContextBuilder:
    def __init__(self, final_context_k: int = 5):
        if final_context_k <= 0:
            raise ValueError(
                "final_context_k must be greater than 0"
            )

        self.final_context_k = final_context_k

    def build(
        self,
        chunks: list[RerankedChunk],
    ) -> BuiltContext:

        selected_chunks = chunks[:self.final_context_k]

        blocks = []

        for reference, chunk in enumerate(
            selected_chunks,
            start=1,
        ):
            metadata = chunk.metadata or {}

            block = ContextBlock(
                reference=reference,
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                source=metadata.get("source"),
                file_type=metadata.get("file_type"),
                page_number=metadata.get("page_number"),
                heading_path=metadata.get("heading_path"),
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