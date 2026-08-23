#load the dataset
import json
from pathlib import Path


def load_evaluation_dataset(
    path: str
) -> list[dict]:

    with open(
        Path(path),
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)