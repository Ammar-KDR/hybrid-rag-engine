from sentence_transformers import SentenceTransformer

from .model import EmbeddingModel
from rag.config import settings


class EmbeddingService:
    def __init__(
        self,
        model_name: str | None = None,
    ):
        model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.model = SentenceTransformer(model_name)


        self.info = EmbeddingModel(
            name=model_name,
            dimension=self.model.get_embedding_dimension(),
        )

    def embed_text(self, text: str) -> list[float]:
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return vector.tolist()

    def embed_texts(self,texts: list[str],) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return vectors.tolist()
    