from pathlib import Path

import pytest

from rag.ingestion.loader import load_document


def test_load_txt_file(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text(
        "Employees must submit expenses within 30 days.",
        encoding="utf-8",
    )

    document = load_document(file_path)

    assert document.text == "Employees must submit expenses within 30 days."
    assert document.file_type == "txt"
    assert document.source == str(file_path)


def test_load_markdown_file(tmp_path: Path):
    file_path = tmp_path / "runbook.md"
    file_path.write_text(
        "# Authentication\n\nERR_AUTH_1042 means the token was revoked.",
        encoding="utf-8",
    )

    document = load_document(file_path)

    assert "ERR_AUTH_1042" in document.text
    assert document.file_type == "md"


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_document("does_not_exist.txt")


def test_unsupported_file_type(tmp_path: Path):
    file_path = tmp_path / "employees.xlsx"
    file_path.write_text("fake spreadsheet", encoding="utf-8")

    with pytest.raises(ValueError):
        load_document(file_path)