from rag.ingestion.pipeline import build_chunks


chunks = build_chunks()

terms = [
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "OOMKilled",
    "imagePullPolicy",
    "ECONNREFUSED",
    "NXDOMAIN",
    "SIGKILL",
    "connection pool",
]


for term in terms:

    matches = [
        c
        for c in chunks
        if term.lower() in c.text.lower()
    ]

    print("=" * 50)
    print(term)
    print("matches:", len(matches))

    for c in matches[:2]:
        print(c.chunk_id)
        print(c.text[:150])