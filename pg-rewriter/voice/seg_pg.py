#!/usr/bin/env python3
"""Control test: is PG's own prose, cut to rewrite-sized passages, in range?

The PG-fit range is derived from whole essays. The rewriter emits ~120 words.
If PG's own 120-word windows also score short, the low rewriter scores are a
short-passage artefact, not the rewriter. If PG's windows sit in range and the
rewriter's don't, it's the rewriter.

Windows real PG essays into ~120-word, sentence-aligned passages, scores each.

    python3 seg_pg.py
"""
import statistics
from pathlib import Path

from build_stats import split_sentences, words
from score import fit, score_text

HERE = Path(__file__).parent
CORPUS = HERE / "corpus"
TARGET_WORDS = 120  # match the rewriter's output length


def windows(text):
    sents = split_sentences(text)
    out, cur, n = [], [], 0
    for s in sents:
        cur.append(s)
        n += len(words(s))
        if n >= TARGET_WORDS:
            out.append(" ".join(cur))
            cur, n = [], 0
    if n >= 60:  # keep a final window only if it's not a stub
        out.append(" ".join(cur))
    return out


def main():
    files = sorted(CORPUS.glob("*.txt"))
    med_sents, fits, in_band, n = [], [], 0, 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        for i, w in enumerate(windows(text)):
            row = score_text(f"{f.stem}{i}", w)
            ms, ft = row["median_sentence_len"], fit(row)
            med_sents.append(ms)
            fits.append(ft)
            if 13 <= ms <= 16:
                in_band += 1
            n += 1

    print(f"PG's own prose in {TARGET_WORDS}-word windows: {n} passages from {len(files)} essays\n")
    print("median sentence length (per window):")
    print(f"  median {statistics.median(med_sents):.1f}  mean {statistics.mean(med_sents):.1f}  "
          f"min {min(med_sents):.1f}  max {max(med_sents):.1f}")
    print(f"  in PG's 13-16 band: {in_band}/{n} ({100*in_band/n:.0f}%)")
    print(f"  below 13: {sum(1 for m in med_sents if m < 13)}/{n} "
          f"({100*sum(1 for m in med_sents if m<13)/n:.0f}%)")
    print("\nPG-fit (per window):")
    print(f"  median {statistics.median(fits):.0f}  mean {statistics.mean(fits):.1f}  "
          f"min {min(fits)}  max {max(fits)}")
    for lo in (90, 85, 80):
        print(f"  >= {lo}: {sum(1 for x in fits if x>=lo)}/{n} ({100*sum(1 for x in fits if x>=lo)/n:.0f}%)")


if __name__ == "__main__":
    main()
