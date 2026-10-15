#!/usr/bin/env python3
"""Validation and Inspection Script for answers.json."""

import json
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent

with open(ROOT_DIR / "answers.json", "r", encoding="utf-8") as f:
    data = json.load(f)

chats = data.get("chats", [])
print(f"Total Chats: {len(chats)}")
total_msgs = sum(len(c.get("messages", [])) for c in chats)
print(f"Total Messages: {total_msgs}")

# Verify schema
valid_schema = True
for c_idx, chat in enumerate(chats):
    if "chat_id" not in chat or "messages" not in chat:
        print(f"[!] Invalid chat structure at index {c_idx}")
        valid_schema = False
    for m_idx, msg in enumerate(chat.get("messages", [])):
        for key in ["message_id", "question", "answer", "contexts"]:
            if key not in msg:
                print(f"[!] Missing key '{key}' in message {msg.get('message_id')}")
                valid_schema = False

print(f"Schema Integrity: {'[VALID]' if valid_schema else '[INVALID]'}")

# Check key answers
print("\n" + "=" * 75)
print(" KEY TEST INSPECTION:")
print("=" * 75)

inspections = [
    "hard-01-1",  # 50 JOD
    "hard-06-1",  # 100 JOD
    "hard-07-1",  # 3 vs 5 JOD
    "hard-13-1",  # 50 JOD guarantee
    "hard-17-1",  # 250 vs 100 JOD
    "hard-20-1",  # ID lost
    "hard-21-1",  # Unclear clarification
    "hard-23-1",  # Out of scope refusal
    "hard-24-1",  # 3 distinct services
    "hard-26-1",  # ID lost 5 JOD
    "hard-29-1",  # Family book first issue 2 JOD
    "hard-29-2",  # Family book first issue SLA (45 min)
    "hard-29-3",  # Family book first issue locations (Civil status offices)
    "hard-30-1",  # ID card damaged 3 JOD
    "hard-30-2",  # ID card damaged no fine
    "hard-31-1",  # Passport renewal, family damaged, id lost
    "hard-32-1",  # Passport photos (2), id card (1), family book (none)
    "hard-33-1",  # Complete checklist
    "hard-36-1",  # ID card first issue 2 JOD
]

msg_map = {}
for chat in chats:
    for msg in chat.get("messages", []):
        msg_map[msg["message_id"]] = msg

for m_id in inspections:
    msg = msg_map.get(m_id)
    if msg:
        print(f"\n[{m_id}] Q: {msg['question']}")
        print(f"--> Contexts count: {len(msg['contexts'])}")
        ans_preview = msg['answer'].replace('\n', ' ')[:200]
        print(f"--> Answer: {ans_preview}...")
