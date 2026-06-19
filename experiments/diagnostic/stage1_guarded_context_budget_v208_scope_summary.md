# stage1_guarded_context_budget_v208 rejection summary

## Decision

V208 does not replace v207 as LTS.

V208 turns the v207 trace-only `16000` char / `32` anchor context-budget audit into actual retrieval behavior. It is clean and answer-safe on the completed full runs, but it is not a better LTS because it does not reduce answer prompt cost and introduces one LME prompt/evidence-row drift by allowing a later short row into the compiler context.

## Full Verification

| Benchmark | answer diff vs v207 | route diff | prompt diff | evidence rows diff | retrieval hits diff | context-budget dropped | answer cache |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `1/500` | `1/500` | `317/500` | avg `2.25` | `499/1/1` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | avg `0.0` | `1540/0/0` |

Inherited judge accuracy would be unchanged because answers are identical, but v208 is not promoted.

## Diagnosis

- LME changed prompt row `47561967aa1ff83faf2853a3` still answered `10-12 hours`, but the budget skipped long unused tail hits and let one later short row enter the prompt.
- LME avg query tokens slightly increased from v207 `6580.196` to v208 `6580.362`; avg context chars also slightly increased from `19775.056` to `19775.478`.
- LoCoMo is a no-op for this budget: avg dropped `0.0`, retrieval hits diff `0/1540`, prompt diff `0/1540`.
- Offline simulation over v207 LME traces suggests a more conservative `22000` char budget preserves prompt-row coverage and avoids the observed prompt-growth risk while still dropping tail candidates on `137/500` LME samples.

## Artifacts

- Config: `configs/stage1_guarded_context_budget_v208_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `ba62b8112df21b203aa46765c7029c9c4b38da7c`
- LME full: `experiments/diagnostic/stage1_guarded_context_budget_v208_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_guarded_context_budget_v208_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_guarded_context_budget_v208_*`

## Next

Try v209 with a more conservative `22000` char context budget and keep the context-budget audit enabled. Promote only if prompt/evidence rows and answers remain identical while retrieval tail candidates are actually reduced.
