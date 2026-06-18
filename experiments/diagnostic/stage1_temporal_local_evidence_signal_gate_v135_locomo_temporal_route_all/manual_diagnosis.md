# V135 LoCoMo Temporal Route-All Diagnosis

## Purpose

Evaluate whether v135 can replace v125 as LTS by reducing goal risk #3: selected-context heuristic over-expansion for temporal local evidence.

V135 keeps v125 retrieval row ids unchanged and adds a hard neighbor signal gate during `temporal_lookup` selected-context materialization.

## Run

- Algorithm commit: `91765709406a81ea2b718948a725912d94bf891f`
- Prediction record commit: `b0f62567226c3ec12519d04ae7bfb93521af4b03`
- Benchmark/subset: LoCoMo `temporal_route_all`, `338` records
- Prediction output: `outputs/diagnostic/stage1_temporal_local_evidence_signal_gate_v135_locomo_temporal_route_all/predictions.jsonl`
- Trace output: `outputs/diagnostic/stage1_temporal_local_evidence_signal_gate_v135_locomo_temporal_route_all/traces.jsonl`
- Dual judge output: `experiments/diagnostic/stage1_temporal_local_evidence_signal_gate_v135_locomo_temporal_route_all/deepseek_dual_judge.json`
- Prompt-changed-only merge: `experiments/diagnostic/stage1_temporal_local_evidence_signal_gate_v135_locomo_temporal_route_all/prompt_changed_only_merge_vs_v125.json`

Clean note: prediction used only question text, raw Memory Context, same-session order, build-memory source links, and prediction-time route. Labels and dual judge outputs were used only offline after prediction.

## Metrics

Direct v135 answer rerun on all 338 temporal records:

| Method | strict | lenient | strict correct | lenient correct |
|---|---:|---:|---:|---:|
| v125 temporal subset | `0.792899` | `0.813609` | `268/338` | `275/338` |
| v135 direct rerun | `0.792899` | `0.807692` | `268/338` | `273/338` |

Prompt-changed-only isolated merge:

| Method | strict | lenient | strict correct | lenient correct |
|---|---:|---:|---:|---:|
| v125 temporal subset | `0.792899` | `0.813609` | `268/338` | `275/338` |
| v135 changed prompts only | `0.781065` | `0.798817` | `264/338` | `270/338` |

The isolated merge is the decision metric because dry-run showed v135 changed prompts on only `189/338` keys. Unchanged prompts should inherit v125 answers/judgments instead of introducing unrelated answer drift.

Token/cost notes:

- Prediction avg query tokens: `5394.988`.
- Answer cache: hits `1`, misses `337`, writes `337`.
- Judge usage total: `309537` tokens across both `deepseek-v4-flash` runs.

## Badcase Pattern

V135 reduces some noisy local context but does so with a hard binary deletion rule. Losses show that weak lexical neighbors can still be essential temporal anchors.

Representative strict/lenient losses:

- `077dc113032925d7209f2c6a`: "When did John go on a camping trip with Max?" v125 answered `Summer 2022`; v135 answered `Summer 2023`.
- `507a52cbe63da61337791db9`: v125 preserved the weekend date for Joanna making ice cream; v135 returned information insufficient after skipping one low-signal neighbor.
- `77c7c748922005d1ca6e8229`: v125 answered `2023-05-27`; v135 returned information insufficient.
- `ab43e3d44c74bef52cd14f1a`: v125 included both summer pride-parade evidence spans; v135 over-selected the August 11 date.
- `ed9f56184e168c4fc79622ef`: v125 answered `April 2023`; v135 shifted to late May 2023.

Representative gains exist, mostly where the removed neighbor reduced distraction:

- `6a00dae1ee0cf6a0b4b91a43`: v135 recovered `2023-10-19`.
- `8136581d7bea1c09edbcc155`: v135 recovered `2023-04-09`.
- `a9b26389e6675bf930f8698f`: v135 recovered `Brazil`.

Net effect is negative: prompt-changed-only paired strict gain/loss `4/8`, lenient gain/loss `4/9`.

## Decision

Reject v135 as an LTS candidate. It has cleaner scope than v124 and reduces one form of selected-context noise, but the hard gate increases recall loss and false insufficiency. It does not satisfy the LTS rule because risk reduction comes with lower dual judge accuracy.

Do not continue v135-style hard neighbor deletion. Future risk #3 work should use softer evidence weighting, route-aware rerank, or answer-side attribution so potentially useful adjacent anchors remain visible but are clearly marked as lower confidence.
