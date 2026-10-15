#!/usr/bin/env python3
"""Run and verify the 6 critical generation tests."""

import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from src.hackathon.corpus import HackathonCorpus
from src.hackathon.router import IntentRouter
from src.hackathon.engine import HackathonEngine

CRITICAL_TESTS = [
    ("Hard 01", "عمري 17 سنة وجوازي باقي عليه 3 شهور. بدي أجدده، قديش الرسوم بالضبط؟ وهل بختلف المبلغ لأنه لسه ما انتهى؟"),
    ("Hard 06", "جوازي انتهى من فترة، وأنا خارج الأردن. بدي أجدد بأقرب وقت؛ وين أراجع، كم المدة، وكم بدفع؟"),
    ("Hard 07", "دفتر العائلة تبعي تالف، مش ضايع. شو بحتاج أجيب؟ وهل في فرق بالرسوم أو الإجراءات عن بدل فاقد؟"),
    ("Hard 13", "الهوية الذكية تبعتي ضاعت، وهاي ثالث مرة. شو لازم أعمل وقديش الرسوم؟ انتبه إذا الرسوم بتتغير حسب عدد مرات الفقدان."),
    ("Hard 17", "أيهما أغلى: جواز سفر بدل فاقد للمرة الثانية أم جواز سفر بدل تالف؟ قارن الرسوم المطبقة على هالحالتين فقط، واذكر أي شرط يغيّر المبلغ."),
    ("Hard 36", "أعطيني الرسوم فقط لإصدار بطاقة ذكية لأول مرة. لا تعطيني رسوم التجديد أو بدل فاقد، ولا تذكر مبلغًا إلا إذا كان مدعومًا بنص من الملفات."),
]

def main():
    corpus = HackathonCorpus()
    router = IntentRouter(corpus)
    engine = HackathonEngine(corpus=corpus, router=router)

    for label, q in CRITICAL_TESTS:
        print("=" * 70)
        print(f"[{label}] {q}")
        res = engine.answer_question(q)
        print("Answer:\n", res["answer"])
        print("\nContexts:")
        for c in res["contexts"]:
            print(" *", c[:80] + "...")
        print()

if __name__ == "__main__":
    main()
