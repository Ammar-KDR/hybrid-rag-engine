import re

from sentence_transformers import SentenceTransformer

from rag.ingestion.model import Chunk, Document


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def split_into_paragraphs(text: str) -> list[str]:
    """
    Split on one or more blank lines.

    We intentionally use paragraphs as the smallest semantic units
    rather than embedding every individual sentence.
    """
    paragraphs = re.split(r"\n\s*\n", text)

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


class SemanticChunker:

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        similarity_threshold: float = 0.55,
        max_chunk_chars: int = 4000,
    ):
        if not -1 <= similarity_threshold <= 1:
            raise ValueError(
                "similarity_threshold must be between -1 and 1"
            )

        self.similarity_threshold = similarity_threshold
        self.max_chunk_chars = max_chunk_chars

        self.model = SentenceTransformer(model_name)


    def chunk(self, document: Document) -> list[Chunk]:

        paragraphs = split_into_paragraphs(document.text)

        if not paragraphs:
            return []

        # Nothing to compare if there is only one paragraph.
        if len(paragraphs) == 1:
            return [
                self._create_chunk(
                    document=document,
                    text=paragraphs[0],
                    chunk_index=0,
                    start_paragraph=0,
                    end_paragraph=0,
                )
            ]

        embeddings = self.model.encode(
            paragraphs,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        chunks = []

        current_paragraphs = [paragraphs[0]]
        start_paragraph = 0

        for i in range(len(paragraphs) - 1):

            current_embedding = embeddings[i]
            next_embedding = embeddings[i + 1]

            similarity = float(
                current_embedding @ next_embedding
            )

            next_paragraph = paragraphs[i + 1]

            candidate_text = "\n\n".join(
                current_paragraphs + [next_paragraph]
            )

            semantic_break = (
                similarity < self.similarity_threshold
            )

            size_break = (
                len(candidate_text) > self.max_chunk_chars
            )

            if semantic_break or size_break:

                chunks.append(
                    self._create_chunk(
                        document=document,
                        text="\n\n".join(current_paragraphs),
                        chunk_index=len(chunks),
                        start_paragraph=start_paragraph,
                        end_paragraph=i,
                    )
                )

                current_paragraphs = [next_paragraph]
                start_paragraph = i + 1

            else:
                current_paragraphs.append(next_paragraph)

        # The loop leaves the final group unfinished,
        # so we append it here.
        chunks.append(
            self._create_chunk(
                document=document,
                text="\n\n".join(current_paragraphs),
                chunk_index=len(chunks),
                start_paragraph=start_paragraph,
                end_paragraph=len(paragraphs) - 1,
            )
        )

        return chunks


    def _create_chunk(
        self,
        document: Document,
        text: str,
        chunk_index: int,
        start_paragraph: int,
        end_paragraph: int,
    ) -> Chunk:

        return Chunk(
            text=text,
            source=document.source,
            file_type=document.file_type,
            chunk_index=chunk_index,
            chunking_strategy="semantic",
            metadata={
                **document.metadata,
                "start_paragraph": start_paragraph,
                "end_paragraph": end_paragraph,
                "similarity_threshold": self.similarity_threshold,
            },
        )