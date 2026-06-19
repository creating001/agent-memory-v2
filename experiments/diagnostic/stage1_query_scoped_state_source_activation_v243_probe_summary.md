# stage1_query_scoped_state_source_activation_v243_probe_summary

## Purpose

验证 v243 是否能把 current-state/update 处理从 query-time `memory_state_guide` prompt block 转为 source-backed retrieval activation：关闭 compiler `memory_state_guide`，启用 query-scoped `memory_slot_chain`，只用 typed memory 选择 raw source rows，answer repair/finalizer 仍 disabled。

## Config

- base LTS: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: `configs/stage1_query_scoped_state_source_activation_v243_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `16486f5e95d3de370663eb033e3f39b595fd3ffe`
- cache seed: v235 prediction-time traces/predictions only; no labels, judge outputs, benchmark tags, sample ids, or test feedback.

## Results

| Scope | n | answer diff vs v235 | slot activation | avg query tokens vs v235 |
|---|---:|---:|---:|---:|
| LME probe50 | 50 | `0/50` | `0/50` | `5677.4 -> 5677.4` |
| LoCoMo probe50 | 50 | `0/50` | `0/50` | `6543.56 -> 6543.56` |
| LME all current_state | 22 | `0/22` | `1/22`, `2` source hits | `10424.045454545454 -> 10410.954545454546` |
| LoCoMo all current_state | 4 | `0/4` | `0/4` | `5947.5 -> 5947.5` |

No changed-answer judge was run because all tested predictions were answer-identical to v235. The current_state targeted run covers every v235 full-run current_state sample in LME and LoCoMo.

## Diagnosis

v243 is clean and low-risk but not useful enough to promote. The prompt-side `memory_state_guide` was already effectively inactive under current gates, and the query-scoped `memory_slot_chain` activation is too narrow: it triggered on only one LME current_state sample and did not change any answer.

The lesson is that simply moving an inactive guide into a conservative activation hook does not make build memory more system-like. The next build-side attempt should improve memory object quality or activation coverage itself, for example by building typed state/update clusters with explicit active/superseded/source evidence and a measurable utility gate, rather than relying on sparse lexical slot overlap.

## Decision

Do not promote v243. Current LTS remains v235.

## Outputs

- LME probe50: `outputs/diagnostic/stage1_query_scoped_state_source_activation_v243_lme_probe50/`
- LoCoMo probe50: `outputs/diagnostic/stage1_query_scoped_state_source_activation_v243_locomo_probe50/`
- LME current_state targeted: `outputs/diagnostic/stage1_query_scoped_state_source_activation_v243_lme_current_state/`
- LoCoMo current_state targeted: `outputs/diagnostic/stage1_query_scoped_state_source_activation_v243_locomo_current_state/`
- targeted inputs: `outputs/diagnostic/stage1_query_scoped_state_source_activation_v243_targeted_inputs/`
