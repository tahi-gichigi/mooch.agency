#!/usr/bin/env python3
"""Sonnet vs gpt-5.5 on the same PG rewriter pipeline: PG-fit + blind judge.

Rewrites the inputs with claude-sonnet-4-6 through the production prompt, scores
each, then runs the same blind judge (gpt-5.1 picks real PG vs the Sonnet
rewrite, both orders).

    OPENAI_API_KEY=... ANTHROPIC_API_KEY=... python3 run_sonnet_compare.py
"""
import json
import os
import urllib.request
from pathlib import Path

from score import fit, score_text
import run_blind_judge as bj  # reuses pg_excerpt(), judge(), SYSTEM

HERE = Path(__file__).parent
SYSTEM = bj.SYSTEM
MODEL = "claude-sonnet-4-6"
AKEY = os.environ["ANTHROPIC_API_KEY"]
SCORE_TOPICS = ["want", "gba", "copy", "ideas", "work"]
JUDGE_TOPICS = ["want", "gba", "copy"]

EXTRA = {  # the two non-corpus candidates (same text as run_sample_search.py)
    "ideas": (HERE / "test" / "ideas_input.txt"),
    "work": (HERE / "test" / "work_input.txt"),
}


def sonnet(text):
    body = json.dumps({"model": MODEL, "max_tokens": 2000, "system": SYSTEM,
                       "messages": [{"role": "user", "content": text.strip()}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": AKEY,
                 "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    return "".join(b.get("text", "") for b in d["content"]).strip()


def src_for(topic):
    p = HERE / "test" / f"bloated_{topic}.txt"
    return p.read_text(encoding="utf-8") if p.exists() else EXTRA[topic].read_text(encoding="utf-8")


def main():
    print(f"writer={MODEL}\n\n=== PG-fit ===")
    print(f"{'topic':6s} {'PG-fit':>7s} {'med-sent':>9s}  (band 13-16)")
    for t in SCORE_TOPICS:
        if t in EXTRA and not EXTRA[t].exists():
            continue
        out = sonnet(src_for(t))
        (HERE / "test" / f"sonnet_{t}.txt").write_text(out + "\n", encoding="utf-8")
        row = score_text(t, out)
        print(f"{t:6s} {fit(row):7d} {row['median_sentence_len']:9.1f}")

    print("\n=== blind judge (gpt-5.1: real PG vs Sonnet rewrite) ===")
    correct = total = 0
    for t in JUDGE_TOPICS:
        pg = bj.pg_excerpt(t)
        rw = (HERE / "test" / f"sonnet_{t}.txt").read_text(encoding="utf-8").strip()
        for pg_pos, (a, b) in (("A", (pg, rw)), ("B", (rw, pg))):
            pick = bj.judge(a, b)
            ok = pick == pg_pos
            correct += ok; total += 1
            print(f"{t:5s} PG={pg_pos} judge={pick} -> {'spotted PG' if ok else 'FOOLED'}")
    print("-" * 40)
    print(f"judge identified real PG: {correct}/{total} ({100*correct/total:.0f}%)")
    print("(gpt-5.5 baseline was 6/6 = 100%)")


if __name__ == "__main__":
    main()
