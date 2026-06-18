#!/usr/bin/env python3
"""Run the PG rewriter through two OpenAI models on the same inputs, for a
head-to-head voice comparison. Mirrors api/rewrite.js request shape (production
system prompt + user text). Saves each rewrite to test/<tag>_<stem>.txt and
prints token usage.

    OPENAI_API_KEY=... python3 run_compare.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SYSTEM = (ROOT / "api" / "pg-system.md").read_text(encoding="utf-8")

MODELS = {"mini": "gpt-5-mini", "gpt55": "gpt-5.5"}
INPUTS = ["bloated_want.txt", "bloated_gba.txt", "bloated_copy.txt"]
MAX_TOKENS = 3000  # headroom over production's 2000 so reasoning models aren't truncated

KEY = os.environ["OPENAI_API_KEY"]


def call(model, text):
    body = json.dumps({
        "model": model,
        "max_completion_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text.strip()},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"content-type": "application/json", "authorization": f"Bearer {KEY}"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    msg = d["choices"][0]["message"]["content"]
    finish = d["choices"][0]["finish_reason"]
    u = d.get("usage", {})
    return msg, finish, u


def main():
    for tag, model in MODELS.items():
        for inp in INPUTS:
            stem = Path(inp).stem.replace("bloated_", "")
            src = (HERE / "test" / inp).read_text(encoding="utf-8")
            try:
                out, finish, u = call(model, src)
            except Exception as e:
                print(f"[{tag}/{stem}] ERROR {e}", file=sys.stderr)
                continue
            outpath = HERE / "test" / f"{tag}_{stem}.txt"
            outpath.write_text((out or "").strip() + "\n", encoding="utf-8")
            rt = u.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
            print(f"[{tag:5s} {model:10s} {stem:5s}] finish={finish:10s} "
                  f"prompt={u.get('prompt_tokens')} completion={u.get('completion_tokens')} "
                  f"reasoning={rt} -> {outpath.name} ({len((out or '').split())} words)")


if __name__ == "__main__":
    main()
