#!/usr/bin/env python3
"""Official Hackathon Entry Point - 42 Irbid AI Future 26 Youth Edition.

Usage:
    python main.py questions.json

Outputs:
    answers.json (valid JSON, UTF-8) adhering strictly to the challenge brief.
"""

import json
import os
import sys
import time
from pathlib import Path

# Ensure 'src' is in python search path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.hackathon.corpus import HackathonCorpus
from src.hackathon.router import IntentRouter
from src.hackathon.engine import HackathonEngine, OUT_OF_SCOPE_REFUSAL


def run_evaluation(input_filepath: Path, output_filepath: Path) -> None:
    print("=" * 65)
    print(" [42 Irbid AI Hackathon] Jordan Civil Status & Passports Chatbot")
    print("=" * 65)
    print(f"[*] Input Questions:  {input_filepath}")
    print(f"[*] Output Answers:   {output_filepath}")

    # Initialize components
    start_init = time.perf_counter()
    corpus = HackathonCorpus()
    router = IntentRouter(corpus)
    engine = HackathonEngine(corpus=corpus, router=router)
    init_time = time.perf_counter() - start_init
    print(f"[*] System initialized with {len(corpus.documents)} services in {init_time:.2f}s\n")

    # Read questions JSON
    with open(input_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    chats = data.get("chats", [])
    total_chats = len(chats)
    total_messages = sum(len(c.get("messages", [])) for c in chats)
    print(f"[*] Processing {total_chats} chats ({total_messages} total messages)...\n")

    processed_chats = []
    msg_counter = 0

    for chat_idx, chat in enumerate(chats, start=1):
        chat_id = chat.get("chat_id", f"chat-{chat_idx:02d}")
        messages = chat.get("messages", [])

        # Every chat is a new user: reset conversation history completely
        history = []
        processed_messages = []

        print(f"--> [Chat {chat_idx}/{total_chats}] {chat_id} ({len(messages)} message{'s' if len(messages) > 1 else ''})")

        for msg in messages:
            msg_counter += 1
            msg_id = msg.get("message_id", f"{chat_id}-{len(processed_messages)+1}")
            question = msg.get("question", "")

            msg_start = time.perf_counter()
            try:
                result = engine.answer_question(question=question, history=history)
                answer = result.get("answer", "")
                contexts = result.get("contexts", [])
            except Exception as e:
                print(f"    [!] Error on message {msg_id}: {e}")
                answer = OUT_OF_SCOPE_REFUSAL
                contexts = []

            msg_elapsed = time.perf_counter() - msg_start

            # Append to conversational memory for follow-up turns in this chat
            history.append({
                "question": question,
                "answer": answer,
                "contexts": contexts,
            })

            # Exact output message format
            msg_out = {
                "message_id": msg_id,
                "question": question,
                "answer": answer,
                "contexts": contexts,
            }
            # Preserve any extra keys from caller
            for k, v in msg.items():
                if k not in msg_out:
                    msg_out[k] = v

            processed_messages.append(msg_out)
            ctx_summary = f"{len(contexts)} context(s)" if contexts else "No context (declined)"
            print(f"    [{msg_counter}/{total_messages}] {msg_id}: \"{question[:40]}...\" ({msg_elapsed:.2f}s, {ctx_summary})")

        processed_chats.append({
            "chat_id": chat_id,
            "messages": processed_messages,
        })

    # Build output payload
    output_payload = {
        "chats": processed_chats
    }

    # Write output JSON as UTF-8
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Successfully generated {output_filepath} ({os.path.getsize(output_filepath)} bytes)")
    print("=" * 65)


def run_interactive() -> None:
    print("=" * 65)
    print(" [Interactive Mode] Jordan Civil Status & Passports Assistant")
    print(" Type your questions in Arabic. Type 'exit' or 'q' to stop.")
    print(" Type 'reset' to start a new chat (clear conversational memory).")
    print("=" * 65)
    corpus = HackathonCorpus()
    router = IntentRouter(corpus)
    engine = HackathonEngine(corpus=corpus, router=router)
    history = []
    while True:
        try:
            q = input("\n[المواطن] > ").strip()
            if not q:
                continue
            if q.lower() in ["exit", "quit", "q"]:
                print("[*] Exiting.")
                break
            if q.lower() in ["reset", "new", "clear"]:
                history = []
                print("[*] تم تصفير الذاكرة وبدء محادثة جديدة.")
                continue
            res = engine.answer_question(q, history=history)
            print(f"\n[المساعد]:\n{res['answer']}")
            if res.get("contexts"):
                print("\n[السياقات المسترجعة]:")
                for c in res["contexts"]:
                    print(f"  * {c.strip()[:100]}...")
            else:
                print("\n[السياقات]: [] (خارج النطاق)")
            history.append({"question": q, "answer": res["answer"], "contexts": res.get("contexts", [])})
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting.")
            break


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["-i", "--interactive", "interactive", "chat"]:
        run_interactive()
        return

    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        # Default fallback if run without arguments
        default_candidate = Path("questions.json")
        if default_candidate.exists():
            input_file = default_candidate
        else:
            print("Usage: python main.py <questions.json>   (or: python main.py -i for interactive mode)")
            sys.exit(1)

    if not input_file.exists():
        print(f"Error: Questions file not found at: {input_file}")
        sys.exit(1)

    output_file = input_file.parent / "answers.json"
    run_evaluation(input_file, output_file)

    # Ensure answers.json is always also available at root working directory
    root_output = Path("answers.json")
    if output_file.resolve() != root_output.resolve():
        try:
            import shutil
            shutil.copy2(output_file, root_output)
            print(f"[*] Also mirrored answers to {root_output.resolve()}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
