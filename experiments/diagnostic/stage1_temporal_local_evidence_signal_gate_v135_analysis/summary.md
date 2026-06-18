# v135 Temporal Local Evidence Signal Gate Analysis

## Purpose

V135 targets goal risk #3: selected-context long/short-turn heuristic and temporal local-context over-expansion. It keeps v125 retrieval row selection unchanged, but only materializes a same-session neighbor when the neighbor has at least one generic signal:

- temporal marker in the neighbor text;
- overlap with non-stopword question terms;
- overlap with non-stopword center-turn terms.

This follows the source-expansion lesson from xMemory-style memory systems: expand from a retrieved source only when the added source carries its own relevance signal. The implementation stays prediction-time only and does not add dataset-specific rules.

## Clean Boundary

- Uses only question text, raw `Memory Context`, same-session turn order, and prediction-time route.
- Does not use gold/reference answers, judge output, benchmark labels, sample ids/qids, row indices, or test feedback.
- Does not change retrieval evidence row ids; it only filters selected-context neighbor text materialization.
- Algorithm commit: `91765709406a81ea2b718948a725912d94bf891f`.
- LoCoMo dry-run record commit: `dacd07ff927105cd3ea907e2ea0d2a23a74c6690`.

## Dry-Run Results

| Benchmark | Joined records | Changed prompts | Changed row ids | Scope note |
|---|---:|---:|---:|---|
| LongMemEval-S full | 500 | 0 | 0 | no selected-context application under this gate |
| LoCoMo non-adversarial full | 1540 | 189 | 0 | all changed prompts are `temporal_lookup`; total skipped low-signal neighbors `339` |

Additional LoCoMo scope:

- `temporal_lookup`: changed prompts `189/338`.
- non-temporal routes: `0` changed prompts.
- full avg context char delta: `-17.564`.
- evidence row delta: `0`.

## Decision

Dry-run scope is clean and route-contained, but the average context reduction is modest. V135 should not be promoted from dry-run evidence alone.

Next step: run LoCoMo `temporal_lookup` route-all answer + paired dual `deepseek-v4-flash` judge. If accuracy is positive, or stays effectively flat while the risk #3 evidence is cleaner, v135 can replace v125 as LTS. If the judge is negative, downgrade v135 and stop adding variants before reviewing badcases.

## Outputs

- LoCoMo dry traces: `outputs/diagnostic/stage1_temporal_local_evidence_signal_gate_v135_locomo_dry/traces.jsonl`
- LME dry traces: `outputs/diagnostic/stage1_temporal_local_evidence_signal_gate_v135_lme_dry/traces.jsonl`
- LoCoMo comparison: `experiments/diagnostic/stage1_temporal_local_evidence_signal_gate_v135_analysis/locomo_vs_v125_trace_comparison.json`
- LME comparison: `experiments/diagnostic/stage1_temporal_local_evidence_signal_gate_v135_analysis/lme_vs_v125_trace_comparison.json`
