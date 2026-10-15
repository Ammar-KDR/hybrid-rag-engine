#!/usr/bin/env python3
"""Targeted Routing Test Suite for questions_hard.json."""

import json
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from src.hackathon.corpus import HackathonCorpus
from src.hackathon.router import IntentRouter


def test_routing():
    corpus = HackathonCorpus()
    router = IntentRouter(corpus)

    with open(ROOT_DIR / "questions_hard.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 80)
    print(" [TESTING ROUTER ON 36 HARD CHATS / 39 MESSAGES]")
    print("=" * 80)

    for chat in data.get("chats", []):
        chat_id = chat.get("chat_id")
        history = []
        for msg in chat.get("messages", []):
            msg_id = msg.get("message_id")
            q = msg.get("question")
            decision = router.route(q, history=history)

            targets_str = ", ".join(
                f"{t.doc_type}_{t.situation} [{'+'.join(t.section_keys)}]"
                for t in decision.targets
            ) if decision.targets else ("UNCLEAR" if decision.is_unclear else "OUT_OF_SCOPE")

            print(f"[{msg_id}] -> {targets_str}")

            # Simulate history with contexts for follow-up testing
            contexts = []
            for t in decision.targets:
                doc = corpus.get_service(t.doc_type, t.situation)
                if doc:
                    for s in t.section_keys:
                        if s in doc.sections:
                            contexts.append(doc.sections[s].context_string)
            history.append({
                "question": q,
                "answer": "Simulated answer",
                "contexts": contexts,
            })


if __name__ == "__main__":
    test_routing()
