from rag.evaluation.gold_correctness_eval import (
    LMStudioCorrectnessJudge,
)


judge = LMStudioCorrectnessJudge()


result = judge.evaluate(
    question=(
        "What does HTTP 429 Too Many Requests mean?"
    ),
    claim=(
        "HTTP 429 indicates that the client "
        "exceeded the allowed request rate."
    ),
    reference_answer=(
        "HTTP 429 means that the client has "
        "exceeded the allowed request rate."
    ),
    required_facts=[
        (
            "HTTP 429 indicates that the client "
            "exceeded the allowed request rate."
        )
    ],
    evidence_spans=[
        (
            "HTTP 429 Too Many Requests indicates "
            "that the client exceeded the allowed "
            "request rate."
        )
    ],
)


print(result)

result = judge.evaluate(
    question=(
        "What does HTTP 429 Too Many Requests mean?"
    ),
    claim=(
        "HTTP 429 indicates that the client exceeded "
        "the allowed request rate and that DNS "
        "resolution failed."
    ),
    reference_answer=(
        "HTTP 429 means that the client has "
        "exceeded the allowed request rate."
    ),
    required_facts=[
        (
            "HTTP 429 indicates that the client "
            "exceeded the allowed request rate."
        )
    ],
    evidence_spans=[
        (
            "HTTP 429 Too Many Requests indicates "
            "that the client exceeded the allowed "
            "request rate."
        )
    ],
)

print(result)

result = judge.evaluate(
    question=(
        "What does HTTP 429 Too Many Requests mean?"
    ),
    claim=(
        "HTTP 429 means that authentication "
        "credentials are invalid."
    ),
    reference_answer=(
        "HTTP 429 means that the client has "
        "exceeded the allowed request rate."
    ),
    required_facts=[
        (
            "HTTP 429 indicates that the client "
            "exceeded the allowed request rate."
        )
    ],
    evidence_spans=[
        (
            "HTTP 429 Too Many Requests indicates "
            "that the client exceeded the allowed "
            "request rate."
        )
    ],
)

print(result)