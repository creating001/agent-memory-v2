# V190 Source-Grounded Self-Reference Selected Context Probe

## Purpose

Evaluate whether temporal selected-context expansion can be narrowed by source-grounded self-reference rather than a blunt question-reference gate.

V190 inherits v184 and only changes temporal selected-context materialization: when the question has no local reference signal, a row is expanded only if the selected turn's speaker role appears in the question, the selected turn is self-referential, and the selected turn covers enough question slot terms. Prediction uses no gold answers, judge output, benchmark labels, sample ids, test feedback, or sample-level rules.

## Run

- Config: `configs/stage1_source_grounded_self_ref_selected_context_v190_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `bb626f269be3371a398a2615d8822cc0ecfdfb32`
- Output: `outputs/diagnostic/stage1_source_grounded_self_ref_selected_context_v190_activation_probe/`
- Experiment record: `experiments/diagnostic/stage1_source_grounded_self_ref_selected_context_v190_activation_probe/`
- Input: `outputs/diagnostic/stage1_segment_local_event_time_candidate_map_v185_activation_probe/input.jsonl`

## Results

| Item | Result |
|---|---:|
| Samples | `3` |
| selected-context applied | `2/3` |
| avg selected-context rows | `2.000` |
| avg query tokens | `5452.000` |
| answer cache | `0/3/3` hits/misses/writes |
| repair/finalizer applied | `0/3` / `0/3` |

Trace effect:

- Jon row: keeps four self-grounded temporal local contexts; answer remains `June 20, 2023`.
- Nate row: keeps the two self-grounded rows `D19:9,D5:10`, skips 29 weaker rows by role/self/coverage reasons, but answer is `2022-08-27 to 2022-08-28`.
- John/James row: selected-context is fully blocked; `D17:29` is skipped as `missing_self_reference`, and answer remains insufficient information.

## Decision

Do not promote V190 to LTS.

The gate improves risk #2/#3 by reducing route-only selected-context expansion and blocking a wrong-speaker local-context binding. However it still loses the current v184 LoCoMo `+1/+1` paired-delta gain because the Nate row answer falls back to the rejected v187/v188 behavior.

Important follow-up: this probe exposed a reproducibility risk. The current codebase has rejected v187 weekend relative-time normalization active globally inside temporal aid/event candidates. That means rerunning the v184 config on current code can differ from the committed v184 LTS output. The next version should move weekend relative-time normalization behind an explicit config flag with default off, and only enable it for the rejected v187/v188 configs that need to reproduce their historical behavior.
