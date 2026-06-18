#!/usr/bin/env python3
"""Concatenate the voice profile and rewrite instruction into the system prompt
the API function loads (api/pg-system.md). Run after editing paulgraham.md or
rewrite.md so the deployed prompt stays in sync.

    python3 build_prompt.py
"""
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent  # repo root

profile = (HERE / "paulgraham.md").read_text()
rewrite = (HERE / "rewrite.md").read_text()

combined = (
    "You rewrite prose in the voice of Paul Graham. Below are two documents: "
    "a VOICE PROFILE describing how he writes, and a REWRITE INSTRUCTION telling "
    "you how to apply that voice to the user's text. Follow both. The user's "
    "message is the text to rewrite. Output only the rewrite.\n\n"
    "=== VOICE PROFILE (paulgraham.md) ===\n\n" + profile +
    "\n\n=== REWRITE INSTRUCTION (rewrite.md) ===\n\n" + rewrite + "\n"
)
out = ROOT / "api" / "pg-system.md"
out.write_text(combined)
print(f"wrote {out} ({len(combined)} chars)")
