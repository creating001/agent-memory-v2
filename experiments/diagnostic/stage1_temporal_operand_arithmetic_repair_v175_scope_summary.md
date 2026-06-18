# V175 Temporal Operand Arithmetic Repair LTS

## Decision

Promote v175 to the current local LTS.

v175 keeps v174's narrow source-grounded temporal/age/duration repair gate, but strengthens the verifier instruction so a derived elapsed-time answer does not need to appear verbatim when all operands are directly supported. It improves both full benchmark patched judge accuracy and reduces #4 over-abstention plus #5 query-time memory reasoning risk without using labels, judge output, benchmark tags, sample ids, test feedback, or sample-level rules in prediction logic.

## Method

- Parent LTS: v173 (`2aad836bfd32f0bc7fb32e066db43e0caee9cf02`).
- Diagnostic parent: v174 (`efd88e46f1ee54c3b838d15c3c809bc1c1cd4083`), which proved the gate was safe but no-op.
- Config: `configs/stage1_temporal_operand_arithmetic_repair_v175_qwen36_no_think_build4k_cached.json`.
- Trigger: `source_grounded_temporal_calculation_review`.
- Trigger scope:
  - routes: `current_state`, `fact_lookup`, `temporal_lookup`;
  - draft answer must be an insufficient-information refusal;
  - question must ask a narrow elapsed-time, age, or duration calculation;
  - blocks multi-part/list/choice/external-name requests;
  - requires source-backed date/duration/age operands in prediction-time `evidence_report`;
  - concrete event endpoint dates exclude `unknown`, `empty`, `N/A`, and ordinary mention-time-only dates.
- Verifier rule: if all operands are directly supported by Memory Context and Question Time, the repair pass may compute elapsed time, age-at-event, or duration; `mention_time` may only resolve an explicit relative time phrase in the same row and cannot act as an event endpoint by itself.

## Full Results

| Benchmark | Answer diff vs v173 | Changed-answer dual judge | Patched full strict/lenient |
|---|---:|---:|---:|
| LongMemEval-S full | `1/500` | `0/1 -> 1/1` | `0.832000 / 0.842000` (`416/500`, `421/500`) |
| LoCoMo non-adversarial full | `1/1540` | `0/1 -> 1/1` | `0.792857 / 0.818182` (`1221/1540`, `1260/1540`) |

Changed answers:

- LME `15d167d1ad74265d5887e5b9`: refusal -> `About 3 weeks ago`.
- LoCoMo `f2f4d77eee321806befb532d`: refusal -> `approximately 3.5 months`.

Both changed samples are judged correct by both independent `deepseek-v4-flash` runs at temperature `0`.

## Cost

- LME avg query tokens: `6260.506`; avg build tokens: `85393.566`; repair triggered/applied `8/3`, repair miss/write `2/2`.
- LoCoMo avg query tokens: `6064.337`; avg build tokens: `62015.574`; repair triggered/applied `5/3`, repair miss/write `2/2`.
- The change remains below the hard query-token limit, but average query tokens are still slightly above the preferred `6k` target. #2 context organization remains an active risk.

## Risk Impact

- #4 over-abstention/source-grounded verifier risk: reduced. v175 repairs directly supported arithmetic refusals while preserving insufficiency when endpoints are missing.
- #5 query-time memory reasoning risk: reduced in a narrow source-backed operand arithmetic surface. Typed/evidence report data still only activates review; final answers depend on Memory Context.
- #1 granularity/profile, #2 top-k/context noise, #3 selected-context generalization, and broader #5 lifecycle/update/conflict reasoning remain open.

## Artifacts

- LME full run: `experiments/diagnostic/stage1_temporal_operand_arithmetic_repair_v175_lme_s_full/`
- LoCoMo full run: `experiments/diagnostic/stage1_temporal_operand_arithmetic_repair_v175_locomo_nonadv_full/`
- Changed-answer judge: `experiments/diagnostic/stage1_temporal_operand_arithmetic_repair_v175_changed_vs_v173/`
- Changed subset predictions/labels: `outputs/diagnostic/stage1_temporal_operand_arithmetic_repair_v175_changed_vs_v173/`
- Full predictions/traces:
  - `outputs/diagnostic/stage1_temporal_operand_arithmetic_repair_v175_lme_s_full/`
  - `outputs/diagnostic/stage1_temporal_operand_arithmetic_repair_v175_locomo_nonadv_full/`
