import re
from .model import GenerationResult, BuiltContext, GeneratedAnswer , Citation
from rag.citation import extract_references


class AnswerBuilder:

    

    def build(
        self,
        question: str,
        generation: GenerationResult,
        context: BuiltContext,
    ) -> GeneratedAnswer:

        references = extract_references(
            generation.text
        )

        citations = []
        unresolved_references=[]
        for reference in references:
            block = context.get_block(reference)

            if block is None:
                unresolved_references.append(reference)
                continue

            citation = Citation(
                reference=reference,
                chunk_id=block.chunk_id,
                source=block.source,
                page_number=block.page_number,
                heading_path=block.heading_path,
            )

            citations.append(citation)

        return GeneratedAnswer(
            question=question,
            answer=generation.text,
            citations=citations,
            unresolved_references=unresolved_references,
            evidence=context.blocks,
            model=generation.model,
            input_tokens=generation.input_tokens,
            output_tokens=generation.output_tokens,
            total_tokens=generation.total_tokens,
            latency_ms=generation.latency_ms,
        )

    