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

        answer_text = generation.text.strip()
        is_insufficient = (
            "insufficient" in answer_text.lower()
            or "available evidence" in answer_text.lower()
            or "not enough evidence" in answer_text.lower()
            or "غير كافية" in answer_text
            or "غير كافٍ" in answer_text
            or "لا توجد أدلة" in answer_text
            or "لا توجد معلومات" in answer_text
        )

        # Fallback: If model generated an answer based on evidence but omitted brackets
        if not citations and context.blocks and not is_insufficient:
            top_block = context.blocks[0]
            citation = Citation(
                reference=top_block.reference,
                chunk_id=top_block.chunk_id,
                source=top_block.source,
                page_number=top_block.page_number,
                heading_path=top_block.heading_path,
            )
            citations.append(citation)
            if f"[{top_block.reference}]" not in answer_text:
                answer_text = f"{answer_text} [{top_block.reference}]"

        return GeneratedAnswer(
            question=question,
            answer=answer_text,
            citations=citations,
            unresolved_references=unresolved_references,
            evidence=context.blocks,
            model=generation.model,
            input_tokens=generation.input_tokens,
            output_tokens=generation.output_tokens,
            total_tokens=generation.total_tokens,
            latency_ms=generation.latency_ms,
        )

    