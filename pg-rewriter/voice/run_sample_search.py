#!/usr/bin/env python3
"""Find a default sample whose gpt-5.5 rewrite reliably scores PG-fit 90+.

The live tool regenerates the rewrite on every click, so a sample is only
"verified 90+" if its rewrites clear 90 consistently, not once. Run each
candidate N times through the production prompt with production params, score
every output, report the spread.

    OPENAI_API_KEY=... python3 run_sample_search.py
"""
import json
import os
import statistics
import urllib.request
from pathlib import Path

from score import fit, score_text

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SYSTEM = (ROOT / "api" / "pg-system.md").read_text(encoding="utf-8")
MODEL = "gpt-5.5"
MAX_TOKENS = 2000  # match production
N = 3
KEY = os.environ["OPENAI_API_KEY"]

# Existing bloated inputs + two new candidates on PG's home turf (ideas, work),
# where the model's PG priors are strongest. Deliberately bloated corporate prose.
CANDIDATES = {
    "copy": (HERE / "test" / "bloated_copy.txt").read_text(encoding="utf-8"),
    "want": (HERE / "test" / "bloated_want.txt").read_text(encoding="utf-8"),
    "gba":  (HERE / "test" / "bloated_gba.txt").read_text(encoding="utf-8"),
    "ideas": (
        "It is frequently observed that individuals who aspire to the founding of "
        "a new venture devote a considerable proportion of their energies to the "
        "deliberate generation of ideas which they imagine might prove commercially "
        "viable. However, it may reasonably be contended that this methodology is, "
        "in a number of respects, fundamentally misguided. The more efficacious "
        "approach would appear to involve the cultivation of a posture of receptivity, "
        "whereby one endeavours to notice the problems and deficiencies that one "
        "encounters in the ordinary course of one's existence, rather than "
        "endeavouring to manufacture solutions in the abstract and in advance of any "
        "demonstrated need."
    ),
    "work": (
        "It is widely propounded, particularly within the context of advice "
        "dispensed to those at an early stage of their professional development, "
        "that the optimal strategy for the attainment of a fulfilling vocation "
        "consists in the relentless pursuit of one's pre-existing passions. It is, "
        "however, arguably the case that such counsel, notwithstanding its "
        "considerable popularity, may in fact prove counterproductive, inasmuch as "
        "the capacity to derive genuine satisfaction from one's labour is, more "
        "often than not, a consequence that emerges subsequent to the acquisition "
        "of demonstrable competence, rather than a precondition that must be "
        "satisfied prior to its commencement."
    ),
}


def call(text):
    body = json.dumps({
        "model": MODEL, "max_completion_tokens": MAX_TOKENS,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": text.strip()}],
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"content-type": "application/json", "authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"]


def main():
    print(f"model={MODEL}  runs={N}  (production params)\n")
    print(f"{'candidate':10s} {'before':>7s} {'runs (PG-fit)':>22s} {'min':>5s} {'median':>7s}")
    print("-" * 60)
    best = None
    for name, src in CANDIDATES.items():
        before = fit(score_text(name, src))
        scores = []
        outs = []
        for i in range(N):
            out = call(src).strip()
            outs.append(out)
            scores.append(fit(score_text(f"{name}{i}", out)))
        mn, med = min(scores), int(statistics.median(scores))
        runs = " ".join(f"{s:3d}" for s in scores)
        print(f"{name:10s} {before:7d} {runs:>22s} {mn:5d} {med:7d}")
        # keep the best run's text + input for any candidate that clears 90 at the floor
        rank = (mn, med)
        if best is None or rank > best[0]:
            best = (rank, name, src, outs[scores.index(max(scores))], max(scores))
        # stash outputs for inspection
        for i, o in enumerate(outs):
            (HERE / "test" / f"search_{name}_{i}.txt").write_text(o + "\n", encoding="utf-8")
    print("-" * 60)
    print(f"\nbest by (min,median): {best[1]} (best single run {best[4]})")


if __name__ == "__main__":
    main()
