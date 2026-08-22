class DuplicateDetector:

    def __init__(
        self,
        vector_store,
        threshold: float = 0.95,
    ):
        self.vector_store = vector_store
        self.threshold = threshold


    def is_duplicate(
        self,
        collection_name: str,
        vector: list[float],
    ) -> bool:

        results = self.vector_store.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=5,
        )

        if not results:
            return False
        
        for result in results:
            print("Duplicate check score:", result.score)

            if result.score >= self.threshold:
                return True
        return False