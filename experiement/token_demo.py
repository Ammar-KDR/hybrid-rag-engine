import tiktoken
def test_token_count():
    encoding = tiktoken.get_encoding("cl100k_base")
    examples = [
        "Hello world",
        "authentication",
        "ERR_AUTH_1042",
        "MAX_RETRY_COUNT",
        "The employee must submit travel expenses within thirty calendar days.",
        "مرحبا كيف حالك",
    ]

    print(encoding.encode(examples[0]))

if __name__ == "__main__":
    test_token_count()
