from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .model import Document


SUPPORTED_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".pdf"}


def normalize_text(text: str) -> str:
    """
    Normalize line endings while preserving document structure.
    """
    return (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )


def load_text_document(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")

    return [
        Document(
            text=normalize_text(text),
            source=str(path),
            file_type=path.suffix.lower().lstrip("."),
        )
    ]


def load_html_document(path: Path) -> list[Document]:
    html = path.read_text(encoding="utf-8")

    soup = BeautifulSoup(html, "lxml")

    # These normally don't contain useful knowledge for our corpus.
    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    text = soup.get_text(separator="\n", strip=True)

    return [
        Document(
            text=normalize_text(text),
            source=str(path),
            file_type="html",
        )
    ]


def load_pdf_document(path: Path) -> list[Document]:
    reader = PdfReader(path)

    documents = []

    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = normalize_text(text)

        # Don't create useless empty documents.
        if not text:
            continue

        documents.append(
            Document(
                text=text,
                source=str(path),
                file_type="pdf",
                metadata={
                    "page_number": page_index + 1,
                    "page_count": len(reader.pages),
                },
            )
        )

    return documents


def load_document(file_path: str | Path) -> list[Document]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Expected a file, received: {path}"
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    if extension in {".txt", ".md"}:
        return load_text_document(path)

    if extension in {".html", ".htm"}:
        return load_html_document(path)

    if extension == ".pdf":
        return load_pdf_document(path)

    # Defensive fallback.
    raise ValueError(
        f"No loader configured for: {extension}"
    )