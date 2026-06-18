#!/usr/bin/env python3
"""
Score arbitrary prose against the Paul Graham voice profile.

Reuses the measurement layer from build_stats.py and the frozen PG profile in
stats.json. Scores against PG's own essay-to-essay RANGE (the 10-90 percentile
band per metric), not a single average: the voice is a range, not a point, so
"inside PG's range" is the honest test. A rewrite can't beat PG by hugging the
mean, and being plainer than PG (less Latinate, fewer hedges, more contractions)
is never penalised.

Give it one or more text files:

    python3 score.py original.txt rewrite.txt [...]

PG-fit is 0-100: 100 means every scored dial sits inside PG's natural range.
Show it before/after, the movement is the story ("your text moved into PG's
range"), not the absolute number.

Note: metrics on short passages are noisier than on whole essays. The five
scored dials are per-word or per-sentence rates that stay indicative on a
paragraph, but a one-sentence input is too short to score meaningfully.
"""

import json
import re
import sys
from pathlib import Path

from build_stats import profile_essay

HERE = Path(__file__).parent
_stats = json.loads((HERE / "stats.json").read_text())
TARGETS = _stats["aggregate"]      # corpus averages, used to scale deviations
RANGES = _stats["ranges"]          # PG's 10-90 percentile band per metric

# (key, label, kind). kind decides how distance outside PG's range is counted:
#   band    = penalise outside the band on either side (too short / too long)
#   floor   = only penalise below the band (more is fine: plainer is PG-like)
#   ceiling = only penalise above the band (less is fine: PG hedges little)
# Only content-independent style dials are scored. Pronoun and question rates
# live in the profile (they guide the rewriter) but depend on the user's topic,
# so they don't belong in a per-rewrite score.
METRICS = [
    ("words", "words", None),
    ("median_sentence_len", "median sentence (words)", "band"),
    ("pct_words_le4", "short words <=4 letters (%)", "floor"),
    ("latinate_rate_pct", "Latinate words (%)", "ceiling"),
    ("hedge_per_1k", "hedges / 1k words", "ceiling"),
    # floor, not band: contractions are an informality marker like short words.
    # More than PG is still PG's direction (more conversational), so it isn't
    # penalised; only too few (formal, uncontracted prose) is un-PG.
    ("contraction_per_1k", "contractions / 1k", "floor"),
]
FIT_KEYS = [(k, kind) for k, _, kind in METRICS if kind]


def score_text(name, text):
    text = re.sub(r"\s+", " ", text).strip()
    return profile_essay(name, text)


def deviation(key, kind, v):
    """0 when inside PG's range; otherwise the distance outside, scaled by the
    corpus average and capped at 1."""
    lo, hi = RANGES[key]["lo"], RANGES[key]["hi"]
    scale = TARGETS[key] or 1
    if kind == "ceiling":
        out = max(0.0, v - hi)
    elif kind == "floor":
        out = max(0.0, lo - v)
    else:  # band
        out = max(0.0, lo - v, v - hi)
    return min(out / scale, 1.0)


def fit(row):
    devs = [deviation(k, kind, row[k]) for k, kind in FIT_KEYS]
    return round(100 * (1 - sum(devs) / len(devs))) if devs else 0


def main():
    files = sys.argv[1:]
    if not files:
        print(__doc__)
        sys.exit(1)
    rows = []
    for f in files:
        p = Path(f)
        rows.append((p.stem, score_text(p.stem, p.read_text(encoding="utf-8"))))

    namew = max(26, max(len(lbl) for _, lbl, _ in METRICS) + 2)
    colw = 12
    header = "metric".ljust(namew) + "".join(n[:colw - 1].rjust(colw) for n, _ in rows)
    header += "PG range".rjust(colw)
    print(header)
    print("-" * len(header))
    for key, label, kind in METRICS:
        line = label.ljust(namew)
        for _, r in rows:
            line += f"{r[key]:>{colw}.2f}" if isinstance(r[key], float) else f"{r[key]:>{colw}}"
        if kind:
            lo, hi = RANGES[key]["lo"], RANGES[key]["hi"]
            line += f"{f'{lo}-{hi}':>{colw}}"
        else:
            line += f"{'':>{colw}}"
        print(line)
    print("-" * len(header))
    fitline = "PG-fit (in-range 0-100)".ljust(namew)
    for _, r in rows:
        fitline += f"{fit(r):>{colw}}"
    print(fitline)


if __name__ == "__main__":
    main()
