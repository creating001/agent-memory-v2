# V142 Scoped Memory State Guide Badcase Summary

## Purpose

Summarize the post-hoc LoCoMo diagnosis for `configs/stage1_scoped_memory_state_guide_v142_qwen36_no_think_build4k_cached.json`.

This diagnosis uses completed prediction traces and offline dual judge records only after prediction. It must not be used to write sample-level prediction rules.

## Formal Result

| Benchmark | strict | lenient | Decision |
|---|---:|---:|---|
| LongMemEval-S full | `408/500 = 0.816000` | `418/500 = 0.836000` | mixed vs fresh v127 `410/500 = 0.820000` strict and `416/500 = 0.832000` lenient |
| LoCoMo non-adversarial full | `1208/1540 = 0.784416` | `1242/1540 = 0.806494` | not promoted; below fresh v127 `1216/1540 = 0.789610` strict and `1256/1540 = 0.815584` lenient |

V142 should not replace v127 as unified LTS: it is only mixed on LongMemEval-S and clearly negative on LoCoMo under the same fresh full dual judge protocol.

## V142 vs V116 LoCoMo Outcome Delta

The comparison below joins v116 and v142 dual judge records by `record_key` for the same 1540 LoCoMo non-adversarial examples.

Strict outcome transitions:

| transition | count |
|---|---:|
| same correct | `1175` |
| same wrong | `307` |
| gain | `33` |
| loss | `25` |

Lenient outcome transitions:

| transition | count |
|---|---:|
| same correct | `1215` |
| same wrong | `270` |
| gain | `27` |
| loss | `28` |

So v142 improves strict relative to v116 (`+8`) but is lenient-neutral to slightly negative (`-1`).

## Where Losses Concentrate

By LoCoMo category, lenient losses/gains vs v116:

| category | gain | loss | note |
|---|---:|---:|---|
| 1 multi-hop | `8` | `15` | main negative area |
| 2 temporal | `12` | `8` | net positive |
| 3 open-domain | `1` | `0` | small positive |
| 4 single-hop | `6` | `5` | near neutral |

By route, lenient losses/gains vs v116:

| route | gain | loss |
|---|---:|---:|
| `fact_lookup` | `3` | `7` |
| `list_count` | `6` | `9` |
| `profile_preference` | `4` | `3` |
| `temporal_lookup` | `14` | `9` |
| `current_state` | `0` | `0` |

## Guide-Subset Finding

The scoped `Managed Memory State Guide` appears in `50/1540` LoCoMo prompts:

| route | category distribution |
|---|---|
| `current_state` | category 2: `1`, category 4: `2`, category 1: `1` |
| `profile_preference` | category 1: `11`, category 4: `34`, category 3: `1` |

On this guide subset, v142 is not the main source of LoCoMo regression:

| subset | strict gain/loss | lenient gain/loss |
|---|---:|---:|
| guide prompts | `+4 / -2` | `+4 / -3` |
| non-guide prompts | `+29 / -23` | `+23 / -25` |

Interpretation: the narrow guide is mostly safe and slightly positive on its own. The unified LoCoMo shortfall is dominated by non-guide changed behavior inherited from the broader v126/v127/v142 route/context stack and by multi-hop/list-count synthesis, not by the 50 guide prompts alone.

## Design Implications

- Do not widen `memory_state_guide` back toward v141. V141 was too broad and would likely add noise.
- Do not treat risk #5 as solved by a source-linked guide. Risk #5 remains broader: memory lifecycle, state update, conflict/version handling, as-of retrieval, and query-time memory reasoning.
- The next #5 candidate should be conflict/as-of state retrieval rather than a larger prompt section:
  - expose compact version chains only when the query asks about current/changed state or explicitly needs update reasoning;
  - keep raw evidence rows as the final answer source;
  - avoid touching LoCoMo multi-hop/list-count prompts unless the retrieval evidence actually changes in a controlled, source-backed way.
- Multi-hop losses suggest the compiler should not add extra memory structure that competes with cross-session evidence synthesis. Any next compiler change should be paired with a route-limited dry-run and changed-answer judge before full formal evaluation.

## Clean Boundary

- Prediction did not read gold answers, judge outputs, benchmark labels, sample ids, row indices, or test feedback.
- This diagnosis reads offline judge records only after prediction and is for aggregate error analysis.
- The conclusions above must remain method-level; they cannot become per-sample fixes.
