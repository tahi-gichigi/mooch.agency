#!/usr/bin/env python3
"""
Deterministic build-time scraper + statistical profiler for the Paul Graham
voice profile.

What it does, in order:
  1. Fetch each essay in the manifest from paulgraham.com (http -> https,
     browser UA, follow redirects).
  2. Extract the essay body: the largest <font size="2" face="verdana"> block,
     with a fallback to the largest <font size="2"> block.
  3. Strip <blockquote> (others' words PG quotes/mocks), the leading date line
     ("October 2015") and any leading parenthetical note, and the trailing
     "Thanks to ..." acknowledgement.
  4. Collapse whitespace, then run a per-essay word-count sanity check.
  5. Count the whole statistical layer. A script counts exactly; a model
     guesses. The stats are what stop pastiche.

Outputs:
  corpus/<slug>.txt   clean essay text (gitignored, regenerable)
  stats.json          per-essay + aggregate numbers, pre-filled into the profile

Run: python3 build_stats.py
Stack: requests + BeautifulSoup. No headless browser: the site is static 2001
HTML, the full text is in the raw response.
"""

import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).parent
CORPUS = HERE / "corpus"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")

# Sampling rule (stated, per the brief): PG's canonical argumentative/opinion
# essays spanning 2004-2026, the register the rewriter actually targets.
# Excluded: Lisp/programming-technical essays (avg.html, power.html), pure
# list-format pieces, and the holdout set below. Voice is constant across
# eras, so this is a sample on a rule, not a weighted corpus.
SAMPLE = [
    "love.html",            # How to Do What You Love
    "makersschedule.html",  # Maker's Schedule, Manager's Schedule
    "ds.html",              # Do Things that Don't Scale
    "disagree.html",        # How to Disagree
    "identity.html",        # Keep Your Identity Small
    "top.html",             # The Top Idea in Your Mind
    "cities.html",          # Cities and Ambition
    "nerds.html",           # Why Nerds are Unpopular
    "hs.html",              # What You'll Wish You'd Known
    "wealth.html",          # How to Make Wealth
    "say.html",             # What You Can't Say
    "procrastination.html", # Good and Bad Procrastination
    "vb.html",              # Life is Short
    "schlep.html",          # Schlep Blindness
    "determination.html",   # The Anatomy of Determination
    "mean.html",            # Mean People Fail
    "earn.html",            # How to Earn a Billion Dollars (reference)
    "before.html",          # Before the Startup
    "good.html",            # Be Good
    "re.html",              # The Refragmentation
]

# Held out of the sample. Used later to validate capture vs flattery
# (strip to core claims, run through the tool, compare to what PG wrote).
HOLDOUT = [
    "gap.html",             # Mind the Gap
    "gba.html",             # General and Surprising
    "copy.html",            # Copy What You Like
    "want.html",            # What Doesn't Seem Like Work
]

MONTHS = ("January|February|March|April|May|June|July|August|September|"
          "October|November|December")
DATE_RE = re.compile(r"^\s*(?:" + MONTHS + r")\s+\d{4}\s*", re.I)
LEAD_PAREN_RE = re.compile(r"^\s*\([^)]*\)\s*")
THANKS_RE = re.compile(r"\s*Thanks to\b.*$", re.S)
# Site nav banner injected at the top of some essays. Not PG's prose.
BANNER_RE = re.compile(
    r"^\s*Want to start a startup\?\s*Get funded by Y Combinator\.\s*", re.I)
# Trailing footnote section. The section header is "Notes" followed by the
# first footnote definition "[1]"; cut from there. Anchoring on [1] (not any
# [n]) avoids truncating at an inline footnote reference mid-body. Citations and
# others' quoted words live here, a different register from the argumentative
# body, same spirit as stripping <blockquote>. Inline [n] markers go too.
NOTES_RE = re.compile(r"\bNotes\b\s*(?=\[1\])")
FOOTNOTE_MARK_RE = re.compile(r"\s*\[\d+\]")
TRAILING_LINK_RE = re.compile(r"\s*Comment on this essay\.\s*$", re.I)

# Sentence splitter. Protect only abbreviations that reliably sit mid-sentence
# and are followed by a capitalised word (titles, e.g./i.e., vs., St.), so the
# splitter doesn't break inside them. Abbreviations that are commonly
# sentence-final (etc., Inc., U.S., No.) are deliberately NOT protected: the
# splitter only breaks before a capital, so their lowercase continuations are
# never mis-split, while their genuinely sentence-final uses now split
# correctly. (Protecting them destroyed the period and merged sentences.)
ABBR = {"e.g.": "e\x00g\x00", "i.e.": "i\x00e\x00", "Mr.": "Mr\x00",
        "Mrs.": "Mrs\x00", "Ms.": "Ms\x00", "Dr.": "Dr\x00",
        "vs.": "vs\x00", "St.": "St\x00"}

# Hedging markers. "sort"/"kind" are only hedges in "sort of"/"kind of", which
# are in HEDGE_PHRASES; keeping them as single tokens too would double-count
# those and misread "a kind person" / "sort the list" as hedges.
HEDGE_WORDS = {
    "maybe", "perhaps", "possibly", "probably", "somewhat", "fairly",
    "rather", "quite", "arguably", "presumably", "relatively", "slightly",
    "seemingly", "apparently", "roughly", "likely",
    "supposedly", "conceivably", "ostensibly",
}
HEDGE_PHRASES = [
    "i think", "i guess", "i suppose", "it seems", "seems to", "tends to",
    "sort of", "kind of", "more or less", "in a sense", "to some extent",
    "i believe", "it could be argued", "one might say",
]

# Latinate-suffix heuristic. Honest proxy, not etymology: these endings mark
# the Latin/French-derived register PG mostly avoids. Gated on word length in
# is_latinate() so monosyllables with accidental endings (give, live, late,
# date, rate, state) don't register. Reported as a rate.
LATINATE_SUFFIX_RE = re.compile(
    r".+(tion|sion|ment|ity|ous|ate|ive|ize|ise|ical|ence|ance|"
    r"able|ible|ism|ist|fic|ude|ary|ory)$")

FIRST_SINGULAR = {"i", "me", "my", "mine", "myself"}
FIRST_PLURAL = {"we", "us", "our", "ours", "ourselves"}
SECOND = {"you", "your", "yours", "yourself", "yourselves"}


def fetch(slug):
    url = "http://www.paulgraham.com/" + slug
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30,
                     allow_redirects=True)
    r.raise_for_status()
    return r.content


def extract_body(html):
    soup = BeautifulSoup(html, "html.parser")
    candidates = soup.find_all("font", attrs={"size": "2", "face": "verdana"})
    if not candidates:
        candidates = soup.find_all("font", attrs={"size": "2"})
    if not candidates:
        return None
    node = max(candidates, key=lambda f: len(f.get_text()))
    for bq in node.find_all("blockquote"):
        bq.decompose()
    # separator=" " so text from adjacent tags and across paragraph breaks
    # doesn't run together (PG's markup leaves no space at <p>/<br> boundaries,
    # which would merge sentences like "billionaires.The")
    text = node.get_text(separator=" ")
    return text


def clean(text):
    # normalise whitespace and the spacing artefacts get_text(separator) leaves
    # around punctuation, so every later regex sees clean single-spaced prose
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:?!])", r"\1", text)  # no space before punctuation
    text = re.sub(r"\[\s*(\d+)\s*\]", r"[\1]", text)  # footnote marks: [ 1 ]->[1]
    text = text.strip()
    # cut the trailing footnote section (it can sit before or after the
    # "Thanks to" line), then the acknowledgement and trailing link
    text = NOTES_RE.split(text)[0]
    text = THANKS_RE.sub("", text)
    text = TRAILING_LINK_RE.sub("", text)
    # leading site banner, then date, then any leading parenthetical note
    text = BANNER_RE.sub("", text)
    text = DATE_RE.sub("", text)
    text = LEAD_PAREN_RE.sub("", text)
    # inline footnote reference markers
    text = FOOTNOTE_MARK_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text):
    t = text
    for k, v in ABBR.items():
        t = t.replace(k, v)
    parts = re.split(r"(?<=[.!?])\s+(?=[\"“(]?[A-Z0-9])", t)
    out = []
    for p in parts:
        for k, v in ABBR.items():
            p = p.replace(v, k)
        p = p.strip()
        if p:
            out.append(p)
    return out


WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")


def words(text):
    return WORD_RE.findall(text)


def per_thousand(count, total):
    return round(count / total * 1000, 2) if total else 0.0


def is_latinate(word):
    # length gate so monosyllables with accidental endings (give, live, late,
    # date, rate, state) don't count; the real Latinate words are 6+ letters
    return len(word) >= 6 and LATINATE_SUFFIX_RE.match(word.lower()) is not None


def profile_essay(slug, text):
    sents = split_sentences(text)
    sent_lens = [len(words(s)) for s in sents]
    sent_lens = [n for n in sent_lens if n > 0]
    toks = words(text)
    lower = [w.lower() for w in toks]
    total = len(toks)

    word_lens = [len(w) for w in toks]
    n_le4 = sum(1 for n in word_lens if n <= 4)
    n_ge8 = sum(1 for n in word_lens if n >= 8)
    sum_word_len = sum(word_lens)
    latinate = sum(1 for w in toks if is_latinate(w))

    first_s = sum(1 for w in lower if w in FIRST_SINGULAR)
    first_p = sum(1 for w in lower if w in FIRST_PLURAL)
    second = sum(1 for w in lower if w in SECOND)

    hedge_tok = sum(1 for w in lower if w in HEDGE_WORDS)
    joined = " " + " ".join(lower) + " "
    hedge_phr = sum(joined.count(" " + p + " ") for p in HEDGE_PHRASES)
    hedge = hedge_tok + hedge_phr

    questions = sum(1 for s in sents if s.rstrip().endswith("?"))
    contractions = sum(1 for w in toks if "'" in w)
    semicolons = text.count(";")
    colons = text.count(":")
    commas = text.count(",")
    dashes = len(re.findall(r"\s-\s|--|—", text))

    openers = Counter()
    for s in sents:
        w = words(s)
        if w:
            openers[w[0].lower()] += 1

    # raw integer tallies kept under "_counts" so aggregate() can pool exact
    # counts across essays instead of re-deriving from rounded percentages
    counts = {
        "words": total, "sentences": len(sents), "sent_lens": sent_lens,
        "sum_word_len": sum_word_len, "n_le4": n_le4, "n_ge8": n_ge8,
        "latinate": latinate, "first_s": first_s, "first_p": first_p,
        "second": second, "hedge": hedge, "contractions": contractions,
        "semicolons": semicolons, "colons": colons, "commas": commas,
        "dashes": dashes, "questions": questions,
    }

    return {
        "slug": slug,
        "words": total,
        "sentences": len(sents),
        "median_sentence_len": statistics.median(sent_lens) if sent_lens else 0,
        "mean_sentence_len": round(statistics.mean(sent_lens), 2) if sent_lens else 0,
        "pct_sent_under_10w": round(sum(1 for n in sent_lens if n < 10) / len(sent_lens) * 100, 1) if sent_lens else 0,
        "pct_sent_10_25w": round(sum(1 for n in sent_lens if 10 <= n <= 25) / len(sent_lens) * 100, 1) if sent_lens else 0,
        "pct_sent_over_25w": round(sum(1 for n in sent_lens if n > 25) / len(sent_lens) * 100, 1) if sent_lens else 0,
        "max_sentence_len": max(sent_lens) if sent_lens else 0,
        "mean_word_len": round(sum_word_len / total, 2) if total else 0,
        "pct_words_le4": round(n_le4 / total * 100, 1) if total else 0,
        "pct_words_ge8": round(n_ge8 / total * 100, 1) if total else 0,
        "latinate_rate_pct": round(latinate / total * 100, 2) if total else 0,
        "first_singular_per_1k": per_thousand(first_s, total),
        "first_plural_per_1k": per_thousand(first_p, total),
        "second_person_per_1k": per_thousand(second, total),
        "hedge_per_1k": per_thousand(hedge, total),
        "question_rate_pct": round(questions / len(sents) * 100, 1) if sents else 0,
        "contraction_per_1k": per_thousand(contractions, total),
        "commas_per_sentence": round(commas / len(sents), 2) if sents else 0,
        "semicolons_per_1k_words": per_thousand(semicolons, total),
        "colons_per_1k_words": per_thousand(colons, total),
        "dashes_per_1k_words": per_thousand(dashes, total),
        "openers": dict(openers.most_common(15)),
        "_counts": counts,
    }


def aggregate(rows):
    """Corpus-level numbers, computed from pooled exact counts (the per-essay
    "_counts" tallies and sentence-length lists), not by re-weighting rounded
    per-essay percentages. Length-stats are over every sentence pooled, so a
    long essay contributes proportionally and the corpus median is the true
    median, not a median of per-essay medians."""
    c = {k: sum(r["_counts"][k] for r in rows)
         for k in ("words", "sentences", "sum_word_len", "n_le4", "n_ge8",
                   "latinate", "first_s", "first_p", "second", "hedge",
                   "contractions", "semicolons", "colons", "commas", "dashes",
                   "questions")}
    sent_lens = [n for r in rows for n in r["_counts"]["sent_lens"]]
    tw, ts = c["words"], c["sentences"]

    def per1k(n):
        return round(n / tw * 1000, 2)

    agg = {
        "essays": len(rows),
        "total_words": tw,
        "total_sentences": ts,
        "mean_essay_words": round(tw / len(rows)),
        "median_sentence_len": statistics.median(sent_lens),
        "mean_sentence_len": round(statistics.mean(sent_lens), 2),
        "pct_sent_under_10w": round(sum(1 for n in sent_lens if n < 10) / ts * 100, 1),
        "pct_sent_10_25w": round(sum(1 for n in sent_lens if 10 <= n <= 25) / ts * 100, 1),
        "pct_sent_over_25w": round(sum(1 for n in sent_lens if n > 25) / ts * 100, 1),
        "max_sentence_len": max(sent_lens),
        "mean_word_len": round(c["sum_word_len"] / tw, 2),
        "pct_words_le4": round(c["n_le4"] / tw * 100, 2),
        "pct_words_ge8": round(c["n_ge8"] / tw * 100, 2),
        "latinate_rate_pct": round(c["latinate"] / tw * 100, 2),
        "first_singular_per_1k": per1k(c["first_s"]),
        "first_plural_per_1k": per1k(c["first_p"]),
        "second_person_per_1k": per1k(c["second"]),
        "hedge_per_1k": per1k(c["hedge"]),
        "contraction_per_1k": per1k(c["contractions"]),
        "semicolons_per_1k_words": per1k(c["semicolons"]),
        "colons_per_1k_words": per1k(c["colons"]),
        "dashes_per_1k_words": per1k(c["dashes"]),
        "question_rate_pct": round(c["questions"] / ts * 100, 1),
        "commas_per_sentence": round(c["commas"] / ts, 2),
    }

    openers = Counter()
    for r in rows:
        for w, n in r["openers"].items():
            openers[w] += n
    agg["top_openers"] = {w: round(n / ts * 100, 1)
                          for w, n in openers.most_common(20)}
    return agg


def run(slugs):
    rows = []
    for slug in slugs:
        try:
            html = fetch(slug)
        except Exception as e:
            print(f"  FAIL fetch {slug}: {e}", file=sys.stderr)
            continue
        body = extract_body(html)
        if not body:
            print(f"  FAIL extract {slug}: no font block", file=sys.stderr)
            continue
        text = clean(body)
        wc = len(words(text))
        # sanity check: a parse failure must not feed junk into the stats
        if wc < 400:
            print(f"  WARN {slug}: only {wc} words, skipping (parse suspect)",
                  file=sys.stderr)
            continue
        (CORPUS / slug.replace(".html", ".txt")).write_text(text, encoding="utf-8")
        row = profile_essay(slug, text)
        rows.append(row)
        print(f"  ok  {slug:24s} {wc:5d} words  "
              f"median_sent={row['median_sentence_len']:.0f}  "
              f"latinate={row['latinate_rate_pct']:.1f}%")
    return rows


def all_slugs():
    """Every essay linked from articles.html. Drops a few non-essay/technical
    index pages. This is the full-corpus scope for the headline 'we analysed
    everything PG wrote' figure."""
    html = requests.get("http://www.paulgraham.com/articles.html",
                         headers={"User-Agent": UA}, timeout=30).content
    soup = BeautifulSoup(html, "html.parser")
    drop = {"index.html", "articles.html", "rss.html", "arc.html", "bel.html",
            "lisp.html", "books.html", "raq.html", "faq.html"}
    out, seen = [], set()
    for a in soup.find_all("a"):
        h = a.get("href") or ""
        if re.fullmatch(r"[a-z0-9]+\.html", h) and h not in drop and h not in seen:
            seen.add(h)
            out.append(h)
    return out


def corpus_headline():
    """Light pass over the WHOLE corpus: fetch, extract, clean, count. Counts
    only, no per-metric profiling. Backs the marketing claim and the word count
    shown in the UI. The rewriter's targets stay on the curated sample."""
    slugs = all_slugs()
    essays = words_total = sents_total = 0
    for slug in slugs:
        try:
            text = clean(extract_body(fetch(slug)) or "")
        except Exception:
            continue
        wc = len(words(text))
        if wc < 400:
            continue
        essays += 1
        words_total += wc
        sents_total += len(split_sentences(text))
    return {
        "essays_linked": len(slugs),
        "essays_analysed": essays,
        "total_words": words_total,
        "total_sentences": sents_total,
        "source": "every essay linked from paulgraham.com/articles.html",
    }


def pctl(vals, p):
    s = sorted(vals)
    i = max(0, min(len(s) - 1, round((p / 100) * (len(s) - 1))))
    return s[i]


def ranges(rows):
    """PG's own essay-to-essay 10-90 percentile band per scored metric. The
    voice is a range, not a point: scoring against the band (not the mean) is
    fairer and stops a rewrite 'beating PG' by hugging the average."""
    keys = ["median_sentence_len", "pct_words_le4", "latinate_rate_pct",
            "hedge_per_1k", "contraction_per_1k"]
    out = {}
    for k in keys:
        vals = [r[k] for r in rows]
        out[k] = {"lo": pctl(vals, 10), "hi": pctl(vals, 90),
                  "min": round(min(vals), 2), "max": round(max(vals), 2)}
    return out


def main():
    print("SAMPLE:")
    sample_rows = run(SAMPLE)
    print("HOLDOUT (validation, not in profile stats):")
    holdout_rows = run(HOLDOUT)

    agg = aggregate(sample_rows)
    rng = ranges(sample_rows)
    print("FULL CORPUS (headline pass, counts only):")
    headline = corpus_headline()
    print(f"  analysed {headline['essays_analysed']}/{headline['essays_linked']} "
          f"essays, {headline['total_words']:,} words")

    # _counts is internal scaffolding for aggregation; drop before serialising
    for r in sample_rows + holdout_rows:
        r.pop("_counts", None)

    out = {
        "sampling_rule": (
            "PG's canonical argumentative/opinion essays, 2004-2026, the "
            "register the rewriter targets. Excludes Lisp/technical essays, "
            "pure list pieces, and the 4-essay holdout. Sample on a rule, "
            "not weighted: voice is constant across eras."
        ),
        "corpus_headline": headline,
        "sample_essays": [r["slug"] for r in sample_rows],
        "holdout_essays": [r["slug"] for r in holdout_rows],
        "aggregate": agg,
        "ranges": rng,
        "per_essay": sample_rows,
        "holdout_per_essay": holdout_rows,
    }
    (HERE / "stats.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\nwrote stats.json")
    a = out["aggregate"]
    print(f"\nCorpus: {a['essays']} essays, {a['total_words']:,} words")
    print(f"median sentence: {a['median_sentence_len']} words, "
          f"mean {a['mean_sentence_len']}")
    print(f"words <=4 chars: {a['pct_words_le4']}%   latinate: {a['latinate_rate_pct']}%")
    print(f"first-singular/1k: {a['first_singular_per_1k']}   "
          f"second-person/1k: {a['second_person_per_1k']}   "
          f"hedge/1k: {a['hedge_per_1k']}")
    print(f"question rate: {a['question_rate_pct']}%   "
          f"contractions/1k: {a['contraction_per_1k']}")


if __name__ == "__main__":
    main()
