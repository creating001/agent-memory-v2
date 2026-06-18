# V174 Source-Grounded Temporal Calculation Repair

## Decision

Do not promote v174 to LTS.

v174 is clean and narrowly scoped, but it is answer-identical to v173 on both full sets while adding repair calls. It is useful as a diagnostic showing that a source-grounded temporal/age/duration verifier gate is safe at this scope, but the repair prompt is still too conservative for derivable elapsed-time answers.

## Method

- Parent: v173 local LTS (`2aad836bfd32f0bc7fb32e066db43e0caee9cf02`).
- Config: `configs/stage1_source_grounded_temporal_calculation_repair_v174_qwen36_no_think_build4k_cached.json`.
- Added a gated `source_grounded_temporal_calculation_review` repair trigger.
- Trigger scope:
  - routes: `current_state`, `fact_lookup`, `temporal_lookup`;
  - draft answer must be an insufficient-information refusal;
  - question must ask a narrow elapsed-time, age, or duration calculation;
  - blocks multi-part/list/choice/external-name requests;
  - requires source-backed date/duration/age operands in prediction-time `evidence_report`;
  - concrete event endpoint dates exclude `unknown`, `empty`, `N/A`, and ordinary mention-time-only dates.
- Clean setting: no gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used by prediction logic. The evidence report only activates verifier review; final answers still depend on Memory Context and Question Time.

## Full Run Results

| Benchmark | Run | Answer diff vs v173 | Repair miss/write | Decision |
|---|---|---:|---:|---|
| LongMemEval-S full | `stage1_source_grounded_temporal_calculation_repair_v174_lme_s_full` | `0/500` | `2/2` | no judge needed; inherits v173 metrics |
| LoCoMo non-adversarial full | `stage1_source_grounded_temporal_calculation_repair_v174_locomo_nonadv_full` | `0/1540` | `2/2` | no judge needed; inherits v173 metrics |

Inherited v173 main metrics remain:

- LongMemEval-S full strict/lenient: `0.830000 / 0.840000`.
- LoCoMo non-adversarial full strict/lenient: `0.792208 / 0.817532`.

## Cost

- LME avg query tokens: `6260.048`; avg build tokens: `85393.566`.
- LoCoMo avg query tokens: `6064.176`; avg build tokens: `62015.574`.
- Added repair calls are small and remain below the hard query-token limit, but no-answer-diff means the added cost is not justified for LTS.

## Diagnosis

The gate correctly targets a small over-abstention surface:

- LME temporal calculation triggers: `2`.
- LoCoMo temporal calculation triggers: `2`.

However, the verifier kept the draft refusal even when endpoints appeared sufficient for simple arithmetic. The prompt says simple arithmetic is allowed, but it also emphasizes missing endpoint/duration risk; in practice the model still requires the derived duration to be stated verbatim.

The next version should keep the same gate but clarify that, when all operands are directly source-backed, the verifier should not require the final elapsed-time, age, or duration phrase to appear verbatim in Memory Context. It must still keep insufficiency when an endpoint, entity match, or start state is missing.

## Outputs

- LME artifacts: `experiments/diagnostic/stage1_source_grounded_temporal_calculation_repair_v174_lme_s_full/`
- LoCoMo artifacts: `experiments/diagnostic/stage1_source_grounded_temporal_calculation_repair_v174_locomo_nonadv_full/`
- LME predictions/traces: `outputs/diagnostic/stage1_source_grounded_temporal_calculation_repair_v174_lme_s_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_source_grounded_temporal_calculation_repair_v174_locomo_nonadv_full/`
