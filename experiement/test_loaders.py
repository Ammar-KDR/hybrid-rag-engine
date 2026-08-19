from pathlib import Path

import pytest

from rag.ingestion.loader import load_document


def test_load_txt_file(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text(
        "Employees must submit expenses within 30 days.",
        encoding="utf-8",
    )

    documents = load_document(file_path)

    assert len(documents) == 1

    document = documents[0]

    assert document.text == "Employees must submit expenses within 30 days."
    assert document.file_type == "txt"
    assert document.source == str(file_path)


def test_load_markdown_file(tmp_path: Path):
    file_path = tmp_path / "runbook.md"
    file_path.write_text(
        "# Authentication\n\nERR_AUTH_1042 means the token was revoked.",
        encoding="utf-8",
    )

    documents = load_document(file_path)

    assert len(documents) == 1

    document = documents[0]

    assert "# Authentication" in document.text
    assert "ERR_AUTH_1042" in document.text
    assert document.file_type == "md"
    assert document.source == str(file_path)


def test_load_html_file(tmp_path: Path):
    file_path = tmp_path / "page.html"

    file_path.write_text(
        """
        <html>
            <head>
                <style>
                    body { color: red; }
                </style>

                <script>
                    alert("hello");
                </script>
            </head>

            <body>
                <h1>Authentication Guide</h1>
                <p>Refresh tokens can be revoked.</p>
            </body>
        </html>
        """,
        encoding="utf-8",
    )

    documents = load_document(file_path)

    assert len(documents) == 1

    document = documents[0]

    assert "Authentication Guide" in document.text
    assert "Refresh tokens can be revoked." in document.text

    # script/style content should have been removed
    assert 'alert("hello")' not in document.text
    assert "color: red" not in document.text

    assert document.file_type == "html"
    assert document.source == str(file_path)


def test_load_pdf_file():
    file_path = Path("data/raw/Alaauddin_Khader_CV_Combined.pdf")

    documents = load_document(file_path)

    # Loader returns one Document per non-empty PDF page
    assert len(documents) > 0

    page_numbers = []
    page_counts = []

    for document in documents:
        assert document.file_type == "pdf"
        assert document.source == str(file_path)
        assert document.text.strip()

        assert "page_number" in document.metadata
        assert "page_count" in document.metadata

        page_numbers.append(document.metadata["page_number"])
        page_counts.append(document.metadata["page_count"])

    # Pages should remain in original order
    assert page_numbers == sorted(page_numbers)

    # Page numbering is 1-based
    assert page_numbers[0] >= 1

    # Every returned document came from the same PDF
    assert len(set(page_counts)) == 1

    page_count = page_counts[0]

    # A returned page number can never exceed the PDF page count
    assert all(1 <= number <= page_count for number in page_numbers)

    # There may be empty pages that aren't returned
    assert len(documents) <= page_count


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_document("does_not_exist.txt")


def test_unsupported_file_type(tmp_path: Path):
    file_path = tmp_path / "employees.xlsx"
    file_path.write_text(
        "fake spreadsheet",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_document(file_path)