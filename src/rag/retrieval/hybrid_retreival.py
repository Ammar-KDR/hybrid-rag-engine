class HybridRetriever:
    def __init__(
        self,
        dense_retriever,
        bm25_retriever,
        fusion,
        candidate_k: int = 5
    ):
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.fusion = fusion
        self.candidate_k = candidate_k
    def retrieve(
    self,
    query: str,
    top_k: int = 5,
    filter=None
    ):

        dense_results = self.dense_retriever.retrieve(
            query=query,
            top_k=self.candidate_k,
            filter=filter
        )

        bm25_results = self.bm25_retriever.retrieve(
            query=query,
            top_k=self.candidate_k,
            filter=filter
        )


        fused_results = self.fusion.fuse(
            {
                "dense": dense_results,
                "bm25": bm25_results
            }
        )

        return fused_results[:top_k]

        
        