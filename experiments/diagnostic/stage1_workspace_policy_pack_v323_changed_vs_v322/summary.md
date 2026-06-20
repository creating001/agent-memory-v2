# stage1_workspace_policy_pack_v323_changed_vs_v322

Purpose: paired offline judge for the two LoCoMo smoke answers changed by v323 selected-context pack policy.

Inputs:

- Old predictions: `outputs/diagnostic/stage1_workspace_policy_pack_v323_changed_vs_v322/old_v322_predictions.jsonl`
- New predictions: `outputs/diagnostic/stage1_workspace_policy_pack_v323_changed_vs_v322/new_v323_predictions.jsonl`
- Labels: `outputs/diagnostic/stage1_workspace_policy_pack_v323_changed_vs_v322/labels.jsonl`

Changed answers:

- `628d9b1436fa405b91ee2820`: v322 `Counseling and mental health (specifically working with trans people)` -> v323 `Counseling and mental health`.
- `0ef0216553b4eeff9be57e45`: v322 `Caroline is a trans woman who has transitioned and is part of the transgender community.` -> v323 `Caroline is a transgender woman.`

Dual DeepSeek flash judge:

| Prediction set | strict | lenient | Output |
|---|---:|---:|---|
| v322 old | `2/2` | `2/2` | `old_v322_dual_judge.json` |
| v323 new | `2/2` | `2/2` | `new_v323_dual_judge.json` |

Judge setup: `deepseek-v4-flash` twice, temperature `0`, default thinking, `--no-resume`.

Clean note: labels and judge outputs are read only after prediction for offline evaluation. They are not used by retrieval, compiler, answer, verifier, memory build, or cache construction.
