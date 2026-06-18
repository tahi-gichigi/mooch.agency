#!/usr/bin/env python3
"""Blind judge: can an independent model tell the gpt-5.5 rewrite from real PG?

For each topic, pair a real PG excerpt against the gpt-5.5 rewrite of a bloated
input. Show both to a different model (gpt-5.1), unlabelled, in both orders, and
ask which is the genuine Paul Graham. If the judge is near chance (~50% correct),
the rewrite is indistinguishable from PG. If it always picks the real one, the
rewrite is detectable.

    OPENAI_API_KEY=... python3 run_blind_judge.py
"""
import json
import os
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SYSTEM = (ROOT / "api" / "pg-system.md").read_text(encoding="utf-8")
WRITER = "gpt-5.5"
JUDGE = "gpt-5.1"
KEY = os.environ["OPENAI_API_KEY"]
TOPICS = ["want", "gba", "copy"]


def chat(model, messages, max_tokens=2000):
    body = json.dumps({"model": model, "max_completion_tokens": max_tokens,
                       "messages": messages}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"content-type": "application/json", "authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def rewrite(topic):
    src = (HERE / "test" / f"bloated_{topic}.txt").read_text(encoding="utf-8")
    return chat(WRITER, [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": src.strip()}])


def pg_excerpt(topic, target=120):
    text = (HERE / "corpus" / f"{topic}.txt").read_text(encoding="utf-8")
    sents = re.split(r"(?<=[.!?])\s+", text)
    out, n = [], 0
    for s in sents:
        out.append(s); n += len(s.split())
        if n >= target:
            break
    return " ".join(out)


def judge(a, b):
    q = ("Below are two short passages, A and B. One was written by Paul Graham. "
         "The other by an AI imitating his style. Which is the genuine Paul Graham? "
         "Reply with exactly one character: A or B.\n\n"
         f"=== A ===\n{a}\n\n=== B ===\n{b}\n")
    ans = chat(JUDGE, [{"role": "user", "content": q}], max_tokens=2000)
    m = re.search(r"[AB]", ans.upper())
    return m.group(0) if m else "?"


def main():
    correct = total = 0
    for t in TOPICS:
        pg = pg_excerpt(t)
        rw = rewrite(t)
        # round 1: PG=A, round 2: PG=B (swap to control position bias)
        for pg_pos, (a, b) in (("A", (pg, rw)), ("B", (rw, pg))):
            pick = judge(a, b)
            ok = (pick == pg_pos)
            correct += ok; total += 1
            print(f"{t:5s} PG={pg_pos}  judge picked {pick}  -> "
                  f"{'spotted real PG' if ok else 'fooled (picked rewrite)'}")
    print("-" * 50)
    pct = 100 * correct / total
    print(f"judge identified real PG: {correct}/{total} ({pct:.0f}%)")
    print("50% = rewrite indistinguishable from PG; 100% = always detectable")


if __name__ == "__main__":
    main()
