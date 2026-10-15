#!/usr/bin/env python3
"""Quick Single Question Tester for Hackathon."""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure src in path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from src.hackathon.corpus import HackathonCorpus
from src.hackathon.router import IntentRouter
from src.hackathon.engine import HackathonEngine

def main():
    if len(sys.argv) < 2:
        print('الاستخدام: python ask.py "سؤالك باللغة العربية"')
        print('مثال: python ask.py "كم رسوم تجديد جواز السفر؟"')
        sys.exit(1)

    question = sys.argv[1]
    engine = HackathonEngine()
    result = engine.answer_question(question)

    print("\n" + "=" * 50)
    print(f"السؤال: {question}")
    print("=" * 50)
    print(f"الإجابة:\n{result['answer']}")
    print("-" * 50)
    if result.get("contexts"):
        print("السياقات المسترجعة:")
        for c in result["contexts"]:
            print(f" * {c}")
    else:
        print("السياقات: [] (لا يوجد سياق / خارج النطاق)")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
