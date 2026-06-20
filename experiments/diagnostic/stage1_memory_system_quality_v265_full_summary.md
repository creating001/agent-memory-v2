# v265 Memory System Quality Full Summary

## Purpose

Validate a trace-only build-stage memory system upgrade. v265 keeps the v264 prediction path but adds schema and quality metadata to `memory_system_graph`: object schema version, source quality, slot quality, and governance policy.

## Configuration

- config: `configs/stage1_memory_system_quality_v265_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `d163684`
- parent LTS: v264 `configs/stage1_lifecycle_graph_overflow_v264_seeded_qwen36_no_think_build4k_cached.json`
- behavior-affecting retrieval/answer settings: unchanged from v264

The new metadata is trace/diagnosis only. It is not used by retrieval ranking, compiler prompt construction, answer generation, repair, finalizer, verifier, or cache keys.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | answer diff vs v264 | answer cache |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6462.478` | `0/500` | hits/misses/writes `500/0/0` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6094.017532467533` | `0/1540` | hits/misses/writes `1540/0/0` |

Accuracy is inherited from v264 because full answer, prompt, final evidence, retrieval and token costs are identical.

## Build System Quality Metrics

| Benchmark | source-backed records | complete slot-key records | temporal-anchor records | multi-source records | low-confidence records | source-backed slots | active/superseded pair slots |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `115.818` | `115.818` | `115.818` | `23.79` | `0.0` | `89.26` | `5.628` |
| LoCoMo non-adversarial full | `150.91493506493507` | `150.91493506493507` | `150.91493506493507` | `44.46363636363636` | `0.0` | `127.69545454545455` | `5.5285714285714285` |

Quality schema coverage:

```text
LME quality_schema_seen: 500/500
LoCoMo quality_schema_seen: 1540/1540
```

## Diff

v265 vs v264 full:

```text
LME answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0
LoCoMo answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0
```

No changed-answer judge is needed.

## Decision

Promote v265 to local LTS.

Rationale: v265 reduces the build-memory-system risk without changing prediction behavior or cost. It makes the build stage more system-like and auditable while preserving v264's lifecycle-gated raw-source retrieval path.

## Outputs

```text
outputs/diagnostic/stage1_memory_system_quality_v265_lme_full/predictions.jsonl
outputs/diagnostic/stage1_memory_system_quality_v265_lme_full/traces.jsonl
outputs/diagnostic/stage1_memory_system_quality_v265_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_memory_system_quality_v265_locomo_full/traces.jsonl
experiments/diagnostic/stage1_memory_system_quality_v265_lme_full/
experiments/diagnostic/stage1_memory_system_quality_v265_locomo_full/
```

## Next Steps

1. Use the new quality fields to guide build-time schema improvements: validity, confidence calibration, source-span coverage and relation slots.
2. Start retiring query-time compatibility branches that are no longer used by the current LTS path.
3. Keep any future behavior-affecting use of quality signals behind an ablation flag and validate with full diff or changed-answer judge.
