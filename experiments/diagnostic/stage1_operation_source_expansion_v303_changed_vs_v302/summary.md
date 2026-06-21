# v303 Guarded Operation Source Expansion

## Purpose

v303 turns v302's trace-only operation evidence coverage audit into a guarded retrieval action. It consumes `memory_operation_plan_v1` and `memory_query_readiness_manifest_v1`, emits raw `source_id` hits only, and never renders derived memory values as final evidence.

## Runs

- Config: `configs/stage1_operation_source_expansion_v303_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Commit: `9a83ab3dbd2dcd1807619e8b84cc50fb2dd8efae`
- LME formal prediction: `outputs/formal/stage1_operation_source_expansion_v303_lme_s_full_9a83ab3/predictions.jsonl`
- LoCoMo formal prediction: `outputs/formal/stage1_operation_source_expansion_v303_locomo_nonadv_full_9a83ab3/predictions.jsonl`
- Formal experiment records:
  - `experiments/formal/stage1_operation_source_expansion_v303_lme_s_full_9a83ab3/`
  - `experiments/formal/stage1_operation_source_expansion_v303_locomo_nonadv_full_9a83ab3/`
- Note: the LME run summary recorded `dirty=True` because the concurrent LoCoMo formal output directory was untracked while LME was running. Code/config were already committed at `9a83ab3`.

## Diff Scope

- LME: answer/prompt/evidence diff vs v302 = `3/3/3`; operation source expansion applied `9/500`, emitted `14` raw sources.
- LoCoMo: answer/prompt/evidence diff vs v302 = `1/3/3`; operation source expansion applied `3/1540`, emitted `6` raw sources.
- LME avg build/query tokens: `85393.566 / 6376.56`.
- LoCoMo avg build/query tokens: `62015.57402597403 / 6094.018831168831`.

## Judge

Changed-answer subsets were judged for both v302 and v303 with dual `deepseek-v4-flash`, temperature `0`, default thinking.

- LME changed subset: v302 strict/lenient `3/3`; v303 strict/lenient `0/1`.
- LoCoMo changed subset: v302 strict/lenient `1/1`; v303 strict/lenient `1/1`.
- Derived full LME: strict/lenient `0.828000 / 0.842000`, counts `414/500`, `421/500`.
- Derived full LoCoMo: strict/lenient `0.794156 / 0.819481`, counts `1223/1540`, `1262/1540`.

Judge files:

- `lme_v302_changed_dual_judge.json`
- `lme_v303_changed_dual_judge.json`
- `locomo_v302_changed_dual_judge.json`
- `locomo_v303_changed_dual_judge.json`
- `derived_full_metrics.json`

## Diagnosis

v303 is too broad for LME. The bad cases show single weak overlaps such as `work`, `trip`, and `job` activating working-memory active-only profile/relationship/preference slots. Those raw sources are source-backed and clean, but they are not sufficiently slot-specific; tail exchange can still shift answer salience on current-state and temporal questions.

## Decision

Do not promote v303 to LTS. Keep the implementation as an ablation point, but v304 should make source expansion stricter: require lifecycle/conflict usefulness, stronger overlap, and avoid active-only working-memory expansion unless the source chain is already anchored by visible evidence.
