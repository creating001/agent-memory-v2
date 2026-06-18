# V155 Current-State Lifecycle Slot Trigger

## Decision

Do not promote `configs/stage1_current_state_lifecycle_slot_trigger_v155_qwen36_no_think_build4k_cached.json` to LTS. Current LTS remains v154.

V155 inherits v154 and enables a narrower `current_state_lifecycle_review` repair trigger. The trigger excludes advice, order/list, percentage/difference, historical `how long ... before`, and latest-event questions. It only uses prediction-time question text, draft answer JSON, and raw Memory Context.

## Result

| Benchmark | Answer diff vs v154 | Triggered repair | Applied repair | Decision |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0/500` | `8/500` | `2/500` | no accuracy change, higher query token |
| LoCoMo non-adversarial full | `0/1540` | `2/1540` | `0/1540` | no accuracy change, higher query token |

Since predictions are answer-normalized identical to v154 on both full scopes, no changed-answer judge was needed. Metrics are inherited from v154: LongMemEval-S strict/lenient `0.822000 / 0.834000`; LoCoMo non-adversarial strict/lenient `0.789610 / 0.815584`.

Token cost:
- LongMemEval avg query tokens: v155 `6221.322` vs v154 `6179.012`.
- LoCoMo avg query tokens: v155 `6055.431` vs v154 `6047.909`.

## Runs

Prediction runs:
- `outputs/diagnostic/stage1_current_state_lifecycle_slot_trigger_v155_lme_s_full/`
- `outputs/diagnostic/stage1_current_state_lifecycle_slot_trigger_v155_locomo_nonadv_full/`

Human-readable run records:
- `experiments/diagnostic/stage1_current_state_lifecycle_slot_trigger_v155_lme_s_full/`
- `experiments/diagnostic/stage1_current_state_lifecycle_slot_trigger_v155_locomo_nonadv_full/`

## Diagnosis

This diagnostic confirms that the refined lifecycle-slot gate is much safer than the original broad estimate: it removes advice, order/list, calculation, and latest-event false triggers. However, enabling the extra verifier produced no answer changes while adding second-pass repair cost. That is not enough to replace v154 as LTS.

Keep the narrower trigger implementation available for future targeted verifier work, but keep it disabled in the LTS config until it either fixes changed answers or reduces a documented risk without extra cost.

## Clean Note

Prediction does not use gold answers, judge outputs, benchmark labels, sample ids, row indices, or test feedback. No changed-answer judge was run because v155 predictions are identical to v154 predictions.
