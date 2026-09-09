from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalStageEvaluation:
    expected_source_total: int
    expected_source_hits: int
    source_recall: float | None

    evidence_span_total: int
    evidence_span_hits: int
    evidence_span_recall: float | None

    hit: bool | None
    first_relevant_rank: int | None
    mrr: float | None


@dataclass(frozen=True)
class RetrievalEvidenceEvaluation:
    candidate: RetrievalStageEvaluation
    final: RetrievalStageEvaluation


class RetrievalEvidenceEvaluator:

    def evaluate(
        self,
        case,
        candidates,
        reranked_chunks,
    ) -> RetrievalEvidenceEvaluation:

        candidate = self._evaluate_stage(
            case=case,
            chunks=candidates,
        )

        final = self._evaluate_stage(
            case=case,
            chunks=reranked_chunks,
        )

        return RetrievalEvidenceEvaluation(
            candidate=candidate,
            final=final,
        )


    def _evaluate_stage(
        self,
        case,
        chunks,
    ) -> RetrievalStageEvaluation:

        expected_source_total = len(
            case.expected_sources
        )

        evidence_span_total = len(
            case.evidence_spans
        )


        # --------------------------------------------------
        # Expected source / section coverage
        # --------------------------------------------------

        expected_source_hits = 0

        for expected_source in case.expected_sources:

            matched = any(
                self._matches_expected_source(
                    chunk=chunk,
                    expected_source=expected_source,
                )
                for chunk in chunks
            )

            if matched:
                expected_source_hits += 1


        if expected_source_total > 0:

            source_recall = (
                expected_source_hits
                /
                expected_source_total
            )

        else:

            source_recall = None


        # --------------------------------------------------
        # Evidence span coverage
        # --------------------------------------------------

        evidence_span_hits = 0

        for evidence_span in case.evidence_spans:

            matched = any(
                self._matches_evidence_span(
                    chunk=chunk,
                    evidence_span=evidence_span,
                )
                for chunk in chunks
            )

            if matched:
                evidence_span_hits += 1


        if evidence_span_total > 0:

            evidence_span_recall = (
                evidence_span_hits
                /
                evidence_span_total
            )

        else:

            evidence_span_recall = None


        # --------------------------------------------------
        # First relevant rank / MRR
        # --------------------------------------------------

        first_relevant_rank = (
            self._find_first_relevant_rank(
                case=case,
                chunks=chunks,
            )
        )


        if expected_source_total == 0:

            hit = None
            mrr = None

        elif first_relevant_rank is None:

            hit = False
            mrr = 0.0

        else:

            hit = True

            mrr = (
                1.0
                /
                first_relevant_rank
            )


        return RetrievalStageEvaluation(
            expected_source_total=expected_source_total,
            expected_source_hits=expected_source_hits,
            source_recall=source_recall,

            evidence_span_total=evidence_span_total,
            evidence_span_hits=evidence_span_hits,
            evidence_span_recall=evidence_span_recall,

            hit=hit,
            first_relevant_rank=first_relevant_rank,
            mrr=mrr,
        )


    def _find_first_relevant_rank(
        self,
        case,
        chunks,
    ) -> int | None:

        if not case.expected_sources:
            return None


        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            for expected_source in case.expected_sources:

                if self._matches_expected_source(
                    chunk=chunk,
                    expected_source=expected_source,
                ):
                    return index


        return None


    def _matches_expected_source(
        self,
        chunk,
        expected_source,
    ) -> bool:

        metadata = chunk.metadata or {}

        chunk_source = self._normalize_path(
            metadata.get(
                "source",
                "",
            )
        )

        expected_document = self._normalize_path(
            expected_source.document
        )


        if not self._path_matches(
            chunk_source,
            expected_document,
        ):
            return False


        expected_section = (
            expected_source.section
            or ""
        )

        if not expected_section:
            return True


        chunk_section = self._get_chunk_section(
            metadata
        )


        return (
            self._normalize_text(
                chunk_section
            )
            ==
            self._normalize_text(
                expected_section
            )
        )


    def _matches_evidence_span(
        self,
        chunk,
        evidence_span,
    ) -> bool:

        metadata = chunk.metadata or {}


        # --------------------------------------------------
        # Document must match
        # --------------------------------------------------

        chunk_source = self._normalize_path(
            metadata.get(
                "source",
                "",
            )
        )

        evidence_document = self._normalize_path(
            evidence_span.document
        )


        if not self._path_matches(
            chunk_source,
            evidence_document,
        ):
            return False


        # --------------------------------------------------
        # Section must match when supplied
        # --------------------------------------------------

        evidence_section = (
            evidence_span.section
            or ""
        )


        if evidence_section:

            chunk_section = self._get_chunk_section(
                metadata
            )

            if (
                self._normalize_text(
                    chunk_section
                )
                !=
                self._normalize_text(
                    evidence_section
                )
            ):
                return False


        # --------------------------------------------------
        # Compare actual evidence text
        # --------------------------------------------------

        chunk_text = self._normalize_text(
            chunk.text
        )

        evidence_text = self._normalize_text(
            evidence_span.text
        )


        if not chunk_text:
            return False

        if not evidence_text:
            return False


        # Structure-aware chunks may contain the whole
        # evidence span.
        if evidence_text in chunk_text:
            return True


        # Fixed / semantic chunks may split a golden
        # evidence span, so the chunk itself may be a
        # subset of the golden passage.
        if chunk_text in evidence_text:
            return True


        return False


    def _get_chunk_section(
        self,
        metadata,
    ) -> str:

        heading_path = metadata.get(
            "heading_path",
            [],
        )


        if heading_path:

            return " > ".join(
                heading_path
            )


        return metadata.get(
            "heading",
            "",
        )


    def _normalize_path(
        self,
        value,
    ) -> str:

        if not value:
            return ""


        value = str(value)

        value = value.replace(
            "\\",
            "/",
        )

        value = value.strip()

        value = value.lower()


        while value.startswith(
            "./"
        ):
            value = value[2:]


        return value


    def _path_matches(
        self,
        actual,
        expected,
    ) -> bool:

        if actual == expected:
            return True


        # Allows absolute paths later while the golden
        # dataset stores paths such as:
        #
        # data/raw/sample_runbook.md

        return actual.endswith(
            "/" + expected
        )


    def _normalize_text(
        self,
        value,
    ) -> str:

        if not value:
            return ""


        return " ".join(
            str(value)
            .lower()
            .split()
        )