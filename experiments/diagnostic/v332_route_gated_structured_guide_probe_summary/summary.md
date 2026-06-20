# v332 Route-Gated Structured Guide Probe

## Purpose

Test whether query tokens can be reduced without touching raw Memory Context by lowering the Structured Evidence Guide row budget only for direct fact/profile routes.

## Method

- config: `configs/stage1_route_gated_structured_guide_v332_seeded_qwen36_no_think_build4k_cached.json`
- commit: `61bacdc4e85a87a9d9ecf6fc857b24d85ee88efe`
- route overrides:
  - `fact_lookup.structured_guide_max_rows=8`
  - `profile_preference.structured_guide_max_rows=8`
- unchanged: raw Memory Context format, evidence selection, answer JSON contract, verifier, current_state/list_count/temporal structured guide budget
- clean note: no labels, judge output, benchmark tags, sample ids, gold answers, or test feedback enter prediction

## Probe Results

| Scope | avg build tokens | avg query tokens | changed answers vs v288 |
|---|---:|---:|---:|
| LME smoke5 | 92386.0 | 5524.0 | 1/5 |
| LoCoMo smoke5 | 45868.0 | 5919.6 | 1/5 |
| LME probe50 | 86398.54 | 5599.64 | 6/50 |
| LoCoMo probe50 | 45868.0 | 5868.8 | 21/50 |

Output integrity:

- `outputs/diagnostic/v332_lme_probe50/predictions.jsonl`: 50 lines, 0 bad JSON, 0 duplicate keys
- `outputs/diagnostic/v332_lme_probe50/traces.jsonl`: 50 lines, 0 bad JSON
- `outputs/diagnostic/v332_locomo_probe50/predictions.jsonl`: 50 lines, 0 bad JSON, 0 duplicate keys
- `outputs/diagnostic/v332_locomo_probe50/traces.jsonl`: 50 lines, 0 bad JSON

## Changed-Answer Judge

Changed answers were judged with offline dual `deepseek-v4-flash` only on changed subsets.

| Scope | changed answers | v288 strict/lenient correct | v332 strict/lenient correct | Decision |
|---|---:|---:|---:|---|
| LME probe50 changed vs v288 | 6/50 | 4/6, 4/6 | 3/6, 3/6 | regression by 1 changed item |
| LoCoMo probe50 changed vs v288 | 21/50 | 17/21, 17/21 | 16/21, 18/21 | strict regression, lenient gain |

Judge paths:

```text
outputs/diagnostic/v332_lme_probe50_changed_vs_v288/base_dual_judge.json
outputs/diagnostic/v332_lme_probe50_changed_vs_v288/new_dual_judge.json
outputs/diagnostic/v332_locomo_probe50_changed_vs_v288/base_dual_judge.json
outputs/diagnostic/v332_locomo_probe50_changed_vs_v288/new_dual_judge.json
```

## Diagnosis

Route-gating Structured Evidence Guide rows reduced query tokens below 6K, but the gain was small and the answer model still drifted. The changed-answer judge shows strict regressions on both benchmarks. Do not promote v332 to LTS and do not continue max-row micro-tuning as the next main path.

Next query simplification should focus on removing or moving query-time guide layers into build-time memory operations, with a stable answer-visible raw evidence interface. If reducing answer prompt tokens remains necessary, prefer a source-pressure-aware policy that can prove unchanged answer outputs on probe before full runs.

