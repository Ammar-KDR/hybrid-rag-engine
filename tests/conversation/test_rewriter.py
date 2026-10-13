from unittest.mock import patch, MagicMock
from rag.api.schemas.ask import ChatMessage
from rag.conversation.rewriter import QueryRewriter


def test_rewriter_heuristic_triggers():
    rewriter = QueryRewriter()

    history = [
        ChatMessage(role="user", content="What is the refund policy deadline?"),
        ChatMessage(role="assistant", content="The refund deadline is 14 days from purchase."),
    ]

    # No history -> should NOT rewrite
    assert rewriter.should_rewrite("What are the exceptions to it?", []) is False

    # Pronoun present + history -> should rewrite
    assert rewriter.should_rewrite("What are the exceptions to it?", history) is True
    assert rewriter.should_rewrite("Can they extend this?", history) is True
    assert rewriter.should_rewrite("Why is that?", history) is True

    # Short follow-up (< 5 words) -> should rewrite
    assert rewriter.should_rewrite("Any exceptions?", history) is True

    # Standalone specific query -> should NOT rewrite
    standalone = "Explain the complete database backup procedure for production cluster."
    assert rewriter.should_rewrite(standalone, history) is False


def test_rewriter_execution_standalone():
    rewriter = QueryRewriter()
    q = "What is the capital of Jordan?"
    rewritten, was_rewritten = rewriter.rewrite(q, [])
    assert rewritten == q
    assert was_rewritten is False


def test_rewriter_ollama_call_mock():
    rewriter = QueryRewriter()
    history = [
        ChatMessage(role="user", content="Tell me about docker compose volumes."),
        ChatMessage(role="assistant", content="Docker volumes persist data across container restarts."),
    ]

    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = (
        b'{"choices": [{"message": {"content": "\\"How do you backup docker compose volumes?\\""}}]}'
    )

    with patch("urllib.request.urlopen", return_value=mock_response):
        rewritten, was_rewritten = rewriter.rewrite("How do you backup it?", history)
        assert was_rewritten is True
        assert rewritten == "How do you backup docker compose volumes?"


def test_rewriter_arabic_triggers():
    rewriter = QueryRewriter()
    history = [
        ChatMessage(role="user", content="ما هي شروط تجديد جواز السفر؟"),
        ChatMessage(role="assistant", content="شروط تجديد الجواز هي إحضار الهوية ودفع الرسوم."),
    ]

    # Arabic pronoun / elliptical triggers
    assert rewriter.should_rewrite("وماذا عن رسومه؟", history) is True
    assert rewriter.should_rewrite("هل توجد استثناءات فيها؟", history) is True
    assert rewriter.should_rewrite("ما هي؟", history) is True
