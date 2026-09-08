import re


CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def extract_references(
    text: str,
) -> list[int]:

    matches = CITATION_PATTERN.findall(text)

    references = []
    seen = set()

    for match in matches:
        reference = int(match)

        if reference not in seen:
            references.append(reference)
            seen.add(reference)

    return references