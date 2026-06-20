# stage1_workspace_policy_pack_v323_lme_full_changed_vs_v288

## Purpose

Audit v323 against the current v288 LTS on LongMemEval-S full after v323 reduced query tokens via workspace-policy-driven selected-context pack control and aggressive context pressure.

This is an offline evaluation audit. Labels and judge outputs are used only after prediction; prediction, retrieval, compiler, answer, verifier, memory build, and cache construction do not use gold answers, judge output, benchmark labels, sample ids, or test feedback.

## Diff

| Item | Result |
|---|---:|
| Samples | `500` |
| Prompt diff | `383/500` |
| Answer diff | `113/500` |
| Evidence full diff | `380/500` |
| Retrieval hit order diff | `141/500` |
| Avg query tokens | `6455.588 -> 5972.272` |
| Avg context chars | `19804.98 -> 18681.51` |
| v323 context pressure | `305/500` |

## Changed-Answer Judge

DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Prediction set | strict | lenient | Judge outputs |
|---|---:|---:|---|
| old v288 changed subset | `72/113` | `76/113` | `old_v288_dual_judge.json` |
| new v323 changed subset | `56/113` | `63/113` | `new_v323_dual_judge.json` |

If unchanged answers inherit v288 correctness, the projected LongMemEval-S full result for v323 is strict/lenient `401/500` / `410/500`, or `0.802 / 0.820`, below v288 `0.834 / 0.846`.

## Diagnosis

v323 is not an LTS candidate. It reduces LME avg query tokens by about `483`, but the global context-pressure policy changes too many prompts/evidence packs and causes a clear changed-answer judge regression. Losses are not isolated to one route; strict losses appear across temporal, fact, list, current-state, and profile routes.

The safe next step is to keep the build-owned selected-context policy interface, but remove or heavily narrow aggressive global context pressure. Query-token reduction must be source-pressure aware and preserve raw evidence coverage before it can replace v288.

## Paths

- v323 LME full run: `experiments/diagnostic/stage1_workspace_policy_pack_v323_lme_full/`
- Changed predictions: `outputs/diagnostic/stage1_workspace_policy_pack_v323_lme_full_changed_vs_v288/`
- Diff JSON: `changed_summary.json`
