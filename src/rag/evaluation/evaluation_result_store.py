import json
from pathlib import Path

from rag.evaluation.case_evaluation_result import (
    CaseEvaluationResult,
)


class EvaluationResultStore:

    def __init__(
        self,
        path: str,
    ):

        self.path = Path(
            path
        )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


    def append(
        self,
        result: CaseEvaluationResult,
    ) -> None:

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    result.to_dict(),
                    ensure_ascii=False,
                )
            )

            file.write(
                "\n"
            )


    def load_completed_case_ids(
        self,
    ) -> set[str]:

        if not self.path.exists():

            return set()


        case_ids = set()


        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue


                data = json.loads(
                    line
                )


                case_id = data.get(
                    "case_id"
                )


                if case_id:

                    case_ids.add(
                        case_id
                    )


        return case_ids