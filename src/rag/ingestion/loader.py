from pathlib import Path

from .model import Document


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_document(file_path: str | Path) -> Document:
    # Convert the incoming string/path into a Path object
    path = Path(file_path)

    # Make sure the path actually exists
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    # Make sure we were given a file, not a directory
    if not path.is_file():
        raise ValueError(f"Expected a file, but received: {path}")

    # Get the extension, e.g. ".txt" or ".md"
    extension = path.suffix.lower()

    # For Day 1 we only support plain text and Markdown
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    # Read the file from disk and decode it as UTF-8 text
    text = path.read_text(encoding="utf-8")

    # Normalize Windows/Mac/Linux line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove unnecessary whitespace only from the beginning/end
    text = text.strip()

    # Convert our raw file into the common internal Document representation
    return Document(
        text=text,
        source=str(path),
        file_type=extension.lstrip("."),
    )


if __name__ == "__main__":
    document = load_document("data/raw/sample_policy.txt")

    print(document)
    print("\n--- TEXT ---")
    print(document.text)
    print("\n--- SOURCE ---")
    print(document.source)
    print("\n--- FILE TYPE ---")
    print(document.file_type)