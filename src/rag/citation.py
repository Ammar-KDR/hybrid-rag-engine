import re


# Matches [1], [1, 2], [Source 1], [Ref: 2], [Doc 1], etc.
BRACKET_CITATION_PATTERN = re.compile(
    r"\[(?:source|doc|document|ref|reference)?\s*:?\s*(\d+(?:\s*[,;\-]\s*\d+)*)\]",
    re.IGNORECASE,
)

# Fallback for parenthesized citations like (Source 1), (Ref 2)
PAREN_CITATION_PATTERN = re.compile(
    r"\((?:source|doc|document|ref|reference)\s*:?\s*(\d+)\)",
    re.IGNORECASE,
)


def extract_references(
    text: str,
) -> list[int]:
    references = []
    seen = set()

    for match in BRACKET_CITATION_PATTERN.finditer(text):
        for num in re.findall(r"\d+", match.group(1)):
            reference = int(num)
            if reference not in seen:
                references.append(reference)
                seen.add(reference)

    if not references:
        for match in PAREN_CITATION_PATTERN.finditer(text):
            reference = int(match.group(1))
            if reference not in seen:
                references.append(reference)
                seen.add(reference)

    return references