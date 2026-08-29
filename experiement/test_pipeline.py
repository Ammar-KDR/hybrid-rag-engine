from rag.pipeline import RAGPipeline
from rag.factory import create_rag_pipeline
pipeline=create_rag_pipeline()

result=pipeline.run("""How should I optimize Kubernetes resource limits for a production workload?""")


print("=" * 60)
print("ANSWER")
print("=" * 60)
print(result.answer.answer)

print("\n" + "=" * 60)
print("CITATIONS")
print("=" * 60)

for citation in result.answer.citations:
    print(
        f"[{citation.reference}] "
        f"chunk_id={citation.chunk_id} "
        f"source={citation.source}"
    )

print(
    "\nUnresolved references:",
    result.answer.unresolved_references,
)

print("\n" + "=" * 60)
print("PIPELINE OBSERVABILITY")
print("=" * 60)

print("Candidates:", result.candidate_count)
print("Evidence blocks:", result.evidence_count)

print(
    "Retrieval latency:",
    round(result.retrieval_latency_ms, 2),
    "ms",
)

print(
    "Reranking latency:",
    round(result.reranking_latency_ms, 2),
    "ms",
)

print(
    "Generation latency:",
    round(result.generation_latency_ms, 2),
    "ms",
)

print(
    "Total latency:",
    round(result.total_latency_ms, 2),
    "ms",
)

print(
    "Input tokens:",
    result.answer.input_tokens,
)

print(
    "Output tokens:",
    result.answer.output_tokens,
)

print(
    "Total tokens:",
    result.answer.total_tokens,
)