from .metrics import hit_rate_at_k , recall_at_k,precision_at_k,reciprocal_rank


class RetrievalEvaluator:

    def __init__(
        self,
        retriever,
    ):
        self.retriever = retriever


    def evaluate(
        self,
        dataset: list[dict],
        k: int = 5,
    ):

        results = []

        for item in dataset:

            question = item["question"]

            expected_ids = item["expected_chunk_ids"]

            retrieved_chunks = self.retriever.retrieve(
                query=question,
                top_k=k,
            )

            retrieved_ids = [
                chunk.chunk_id
                for chunk in retrieved_chunks
            ]

            hit = hit_rate_at_k(
                retrieved_ids=retrieved_ids,
                expected_ids=expected_ids,
                k=k,
            )
            recall= recall_at_k(
                retrieved_ids=retrieved_ids,
                expected_ids=expected_ids,
                k=k,
            )
            precision = precision_at_k(
                retrieved_ids=retrieved_ids,
                expected_ids=expected_ids,
                k=k,
                )
            mrr=reciprocal_rank(
                retrieved_ids=retrieved_ids,
                expected_ids=expected_ids,

            )

            results.append(
                {
                    "id": item["id"],
                    "question": question,
                    "retrieved_ids": retrieved_ids,
                    "expected_ids": expected_ids,
                    "hit": hit,
                    "recall":recall,
                    "precision":precision,
                    "mrr":mrr,
                }
            )


        score_hit = sum(
            result["hit"]
            for result in results
        ) / len(results)
        
        score_recall = sum(
            result["recall"]
            for result in results
        ) / len(results)
        average_precision = sum(
            result["precision"]
            for result in results
        ) / len(results)
        
        mrr_score = sum(
            result["mrr"]
            for result in results
        ) / len(results)



        return {
            "hit_rate": score_hit,
            "recall_rate":score_recall,
            "avg_precision":average_precision,
            "mrr_score":mrr_score,
            "results": results,
        }