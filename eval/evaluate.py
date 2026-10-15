#!/usr/bin/env python3
"""Automated Hackathon Benchmark Evaluator."""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = ROOT_DIR / "eval" / "eval_questions.json"
GROUND_TRUTH_PATH = ROOT_DIR / "eval" / "eval_ground_truth.json"
ANSWERS_PATH = ROOT_DIR / "eval" / "answers.json"


def normalize_ar(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)  # remove diacritics
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"[ـ]", "", text)  # remove tatweel
    return text.lower().strip()


def run_benchmark():
    print("=" * 70)
    print(" [42 Irbid AI Hackathon] AUTOMATED COMPREHENSIVE BENCHMARK RUNNER")
    print("=" * 70)

    # 1. Run main.py on eval_questions.json
    print(f"[*] Running evaluation pipeline: python main.py {QUESTIONS_PATH.name}...")
    t0 = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        [sys.executable, "main.py", str(QUESTIONS_PATH)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    duration = time.perf_counter() - t0

    if res.returncode != 0:
        print(f"[!] Pipeline failed with return code {res.returncode}:")
        print(res.stderr)
        sys.exit(1)

    print(f"[+] Pipeline executed successfully in {duration:.2f}s\n")

    # 2. Load answers and ground truth
    with open(ANSWERS_PATH, "r", encoding="utf-8") as f:
        answers_data = json.load(f)

    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    # Flatten generated messages
    generated_map = {}
    for chat in answers_data.get("chats", []):
        for msg in chat.get("messages", []):
            generated_map[msg.get("message_id")] = msg

    # 3. Score each message
    results = []
    total_context_score = 0
    total_fact_score = 0

    print("=" * 70)
    print(f" {'ID':<11} | {'Type':<25} | {'Context':<8} | {'Facts':<8} | {'Status'}")
    print("-" * 70)

    for msg_id, gt in ground_truth.items():
        msg = generated_map.get(msg_id)
        if not msg:
            results.append({
                "id": msg_id,
                "type": gt["type"],
                "context_score": 0,
                "fact_score": 0,
                "passed": False,
                "details": "Message missing in output"
            })
            continue

        answer = msg.get("answer", "")
        contexts = msg.get("contexts", [])
        all_ctx_text = " ".join(contexts)

        # A. Context Scoring
        if gt.get("expected_empty_contexts"):
            ctx_passed = len(contexts) == 0
        else:
            required_kw = gt.get("expected_context_keywords", [])
            norm_ctx = normalize_ar(all_ctx_text)
            matches = sum(1 for kw in required_kw if normalize_ar(kw) in norm_ctx)
            ctx_passed = (matches >= len(required_kw) * 0.6) and len(contexts) > 0

        # B. Fact Scoring
        req_facts = gt.get("required_facts", [])
        norm_ans = normalize_ar(answer)
        fact_matches = sum(1 for f in req_facts if normalize_ar(f) in norm_ans)
        fact_passed = fact_matches == len(req_facts) if req_facts else True

        c_score = 100 if ctx_passed else 0
        f_score = 100 if fact_passed else int((fact_matches / len(req_facts)) * 100) if req_facts else 100

        total_context_score += c_score
        total_fact_score += f_score

        overall_pass = ctx_passed and fact_passed
        status_str = "[PASS]" if overall_pass else "[FAIL]"

        print(f" {msg_id:<11} | {gt['type']:<25} | {c_score:>6}% | {f_score:>6}% | {status_str}")

        results.append({
            "id": msg_id,
            "type": gt["type"],
            "question": msg.get("question"),
            "answer": answer,
            "contexts": contexts,
            "reference_answer": gt.get("reference_answer"),
            "context_score": c_score,
            "fact_score": f_score,
            "passed": overall_pass,
        })

    n = len(ground_truth)
    avg_context = total_context_score / n
    avg_facts = total_fact_score / n
    composite_score = (avg_context * 0.4) + (avg_facts * 0.6)

    print("=" * 70)
    print(f"[*] Total Evaluation Cases:     {n}")
    print(f"[*] Context Retrieval Accuracy: {avg_context:.1f}%")
    print(f"[*] Factual Correctness Rate:   {avg_facts:.1f}%")
    print(f"[*] Composite Benchmark Score:  {composite_score:.1f}% / 100%")
    print(f"[*] Average Speed per Query:    {duration / n:.2f} seconds")
    print("=" * 70)

    # Save detailed evaluation report
    report_file = ROOT_DIR / "eval" / "benchmark_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_cases": n,
                "context_accuracy": round(avg_context, 2),
                "factual_accuracy": round(avg_facts, 2),
                "composite_score": round(composite_score, 2),
                "duration_seconds": round(duration, 2),
                "avg_seconds_per_query": round(duration / n, 2),
            },
            "cases": results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Detailed benchmark report saved to: {report_file}")


if __name__ == "__main__":
    run_benchmark()
