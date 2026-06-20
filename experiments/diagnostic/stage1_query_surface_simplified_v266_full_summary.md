# v266 Query Surface Simplified Full Summary

## Purpose

Validate a low-risk LTS cleanup that reduces inactive query-time surface area. v266 keeps the v265 prediction path but makes disabled answer repair/finalizer modules trace as explicitly disabled instead of carrying historical nested trigger/cache settings.

## Configuration

- config: `configs/stage1_query_surface_simplified_v266_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `788a603`
- parent LTS: v265 `configs/stage1_memory_system_quality_v265_seeded_qwen36_no_think_build4k_cached.json`
- behavior-affecting retrieval/answer settings: unchanged from v265

The cleanup is not a benchmark rule and does not use labels, judge outputs, benchmark tags, sample ids, test feedback, gold answers, or sample-level rules.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | answer diff vs v265 | answer cache |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6462.478` | `0/500` | hits/misses/writes `500/0/0` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6094.017532467533` | `0/1540` | hits/misses/writes `1540/0/0` |

Accuracy is inherited from v265 because full answer, prompt, final evidence, retrieval and token costs are identical.

## Diff

v266 vs v265 full:

```text
LME answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0
LoCoMo answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0
```

Probe50 was also answer/prompt/final-evidence/retrieval/token identical before the full runs. No changed-answer judge is needed.

## Risk Reduction

- Default LTS config now exposes `answer.repair` and `answer.finalizer` only as `enabled: false`; historical v234 repair cache and disabled trigger settings are removed from the active LTS config.
- `Stage1Pipeline` no longer parses nested repair/finalizer settings when those modules are disabled, reducing accidental enablement and query-time compatibility risk.
- Experiment `summary.md` and `diagnosis.md` compact disabled auxiliary answer modules to one enabled line plus real applied/trigger/cost counts.
- Repair/finalizer implementations remain available for explicit ablations; useful code was not deleted.

## Decision

Promote v266 to local LTS.

Rationale: v266 reduces query-stage design/maintenance risk while preserving v265 performance, outputs, prompts, retrieval, evidence, and token costs exactly.

## Outputs

```text
outputs/diagnostic/stage1_query_surface_simplified_v266_lme_full/predictions.jsonl
outputs/diagnostic/stage1_query_surface_simplified_v266_lme_full/traces.jsonl
outputs/diagnostic/stage1_query_surface_simplified_v266_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_query_surface_simplified_v266_locomo_full/traces.jsonl
experiments/diagnostic/stage1_query_surface_simplified_v266_lme_full/
experiments/diagnostic/stage1_query_surface_simplified_v266_locomo_full/
```

## Next Steps

1. Continue simplifying query-time compatibility layers that are disabled or trace-only in the current LTS.
2. Move the next substantive improvement back to build-time memory system design: richer object schema, validity, confidence, source spans, merge/supersede and usage utility.
3. Keep performance guarded by full diff or changed-answer paired judge before any LTS promotion.
