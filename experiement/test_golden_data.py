from rag.evaluation.golden_dataset import (
    load_golden_dataset,
)


def main():

    cases = load_golden_dataset(
        "data/evaluation/day10_golden_rag_dataset_v1.json"
    )

    print("Total cases:", len(cases))

    first = cases[0]

    print()
    print("ID:", first.id)
    print("Category:", first.primary_category)
    print("Question:", first.question)
    print("Answerable:", first.answerable)
    print("Reference:", first.reference_answer)

    print("\nRequired facts:")

    for fact in first.required_facts:
        print("-", fact.description)

    print("\nEvidence:")

    for span in first.evidence_spans:
        print("Document:", span.document)
        print("Section:", span.section)
        print("Text:", span.text)


if __name__ == "__main__":
    main()