# stage1_workspace_policy_safe_pack_v324_lme_full_diff_vs_v288

## Purpose

Verify whether v324 preserves the current v288 LTS behavior on LongMemEval-S full while moving selected-context pack control to build-owned `memory_workspace_policy_v1`.

## Diff

| Item | Result |
|---|---:|
| Samples | `500` |
| Prompt diff | `3/500` |
| Answer diff | `1/500` |
| Evidence full diff | `3/500` |
| Retrieval hit order diff | `20/500` |
| Route diff | `0/500` |
| Avg query tokens | `6455.588 -> 6454.482` |
| Avg context chars | `19804.98 -> 19802.802` |

The 3 prompt/evidence changes are exactly the LME full selected-context cases affected by build-owned pack limits. There is no global context pressure in v324.

## Changed-Answer Judge

The only changed answer is:

- `ca58d3822fef67b8df2c3fe3`: `Patagonia and Southwest Airlines` -> `The two companies mentioned are Patagonia and Southwest Airlines.`

DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking:

| Prediction set | strict | lenient |
|---|---:|---:|
| old v288 | `1/1` | `1/1` |
| new v324 | `1/1` | `1/1` |

Judge outputs: `experiments/diagnostic/stage1_workspace_policy_safe_pack_v324_lme_full_changed_vs_v288/`.

## Decision

For LongMemEval-S full, v324 inherits v288 LTS accuracy: strict/lenient remains `417/500` / `423/500`, or `0.834 / 0.846`. Query tokens are essentially unchanged because v324 intentionally removed v323's aggressive global context pressure.

V324 is still not an LTS replacement until LoCoMo full is validated, because LoCoMo selected context changes most prompts.
