# Voice profile validation

How we know the rewriter captures Paul Graham's voice rather than flattering it,
and how the model and prompt were chosen. Bias-controlled throughout.

## Method

The 4 holdout essays (gap, gba, copy, want) are never in the profile's stats, so
they test capture, not memorisation. For each:

1. Bloat the essay's core claim into hedge-heavy, Latinate prose, the kind of
   input the tool exists to fix.
2. Rewrite it through the production prompt (`paulgraham.md` + `rewrite.md`).
3. Score the rewrite against PG's range with `score.py`.
4. Blind-judge it: an independent model picks the genuine PG between the rewrite
   and a real PG excerpt, order swapped to cancel position bias.

## Scoring (range-based)

`score.py` scores against PG's own essay-to-essay 10-90 percentile band per
metric, not a single average. PG varies essay to essay (Latinate 0.85-6.8%,
contractions 17-55/1k), so "inside his range" is the honest test. Floor/ceiling
metrics mean being plainer than PG (fewer hedges, less Latinate) is never
penalised, and a rewrite can't beat PG by hugging the mean. Five content-
independent dials: median sentence length, short-word %, Latinate %, hedges/1k,
contractions/1k.

## Findings

**1. The profile works.** Early bias-controlled run (different subagents bloated,
rewrote, judged, none told the purpose): the profile rewrite beat a plain
"make it concise" control 3/3 blind, with PG-fit climbing from ~15 (bloated) into
PG's range. The profile reaches plainness and concrete rhythm the generic control
doesn't.

**2. Over-correction, found and fixed.** The first rewrites stripped inputs to a
bare skeleton: median sentences of 6-11 words against PG's 13-16, contractions
overshooting. Cause was the cutting licence, not a missing length rule. Fix in
`rewrite.md`: cut filler only, keep the reasoning, develop a bare point the way PG
would. Result on gpt-5.5: median PG-fit rose from the low 80s to ~90 and sentence
length came back into band, prose developed not padded.

**3. Model bake-off (gpt-5.5 chosen).** Same prompt, same inputs, PG-fit:

| input | gpt-5-mini | Sonnet 4.6 | Opus 4.8 | gpt-5.5 |
| --- | --- | --- | --- | --- |
| want | 52 | 85 | 77 | 94 |
| gba | 84 | 77 | 94 | 80 |
| copy | 76 | 81 | 76 | 89 |

gpt-5.5 leads and is most consistent. gpt-5-mini over-compresses and burns heavy
reasoning overhead; Sonnet and Opus run choppier. gpt-5.5 is the v0.1 model.

**4. The blind judge is an AI-text detector, not a PG gate.** Across every model
and input (vague and concrete, same-source and different-source pairings) an
independent judge identified the real PG 18/18. Genuine PG has an idiosyncratic
economy a clean LLM rewrite smooths out, regardless of model, specifics, or
sentence length. So this test answers "was this AI-written?" (always yes), not
"does it read like PG?". We do not gate on it. The tool is judged on mechanics
(PG-fit ~90), human read, and improvement over the input.

**5. Concreteness is the human tell.** On a vague input the rewrite reads generic:
PG's signature move is proof-by-concrete-example, and the no-invention rule
rightly forbids adding examples that aren't there. On a concrete input the tool
keeps the specifics and reads markedly more PG (PG-fit 86-94, sentences in band).
So the tool is strongest on inputs that already carry detail; the demo sample is
deliberately one of those.

## Caveats

- Short passages are noisy: at ~120 words, PG's own essay excerpts only clear
  PG-fit 90 about half the time. Target the median, not a hard floor.
- The score measures mechanics only, not meaning fidelity. No-invention and
  "never reverse the position" are enforced by `rewrite.md`, not by `score.py`.

## Reproduce

```
# score a rewrite against the real essay and the bloated input
python3 score.py test/bloated_copy.txt test/sonnet_copy.txt corpus/copy.txt

# PG's own prose at rewrite length (the range-fairness control)
python3 seg_pg.py

# model bake-off, blind judge, Sonnet/Opus comparison
python3 run_sample_search.py
python3 run_blind_judge.py
python3 run_sonnet_compare.py
```

Fixtures: `test/bloated_*.txt` (inputs), `test/{mini,gpt55,sonnet,opus}_*.txt`
(per-model rewrites), `test/concrete_copy*.txt` and `test/sample_demo.txt`
(concrete-input tests). PG comparison spans come from the gitignored corpus.
