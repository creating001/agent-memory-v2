# v267 Build Memory Governance Full Summary

## Purpose

Validate a build-stage system upgrade. v267 keeps the v266 prediction path but adds a trace-only `memory_system_governance_v1` manifest under `memory_system_graph` so each managed memory object is audited for source-backed activation readiness, raw-evidence-required status, confidence bucket, lifecycle/temporal signals, and risk flags.

## Configuration

- config: `configs/stage1_memory_governance_v267_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `2c4e9f7`
- parent LTS: v266 `configs/stage1_query_surface_simplified_v266_seeded_qwen36_no_think_build4k_cached.json`
- behavior-affecting retrieval/answer settings: unchanged from v266

The governance manifest is trace/diagnosis only. It is not used by retrieval ranking, compiler prompt construction, answer generation, repair, finalizer, verifier, or cache keys.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | answer diff vs v266 | governance schema |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6462.478` | `0/500` | `500/500` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6094.017532467533` | `0/1540` | `1540/1540` |

Accuracy is inherited from v266 because full answer, prompt, final evidence, retrieval and token costs are identical.

## Governance Metrics

| Benchmark | avg activation-ready records | avg governance risk records | risk counts |
|---|---:|---:|---|
| LongMemEval-S full | `115.818` | `0` | `{}` |
| LoCoMo non-adversarial full | `150.91493506493507` | `0` | `{}` |

## Diff

v267 vs v266 full:

```text
LME answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, governance_schema_seen=500/500
LoCoMo answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, governance_schema_seen=1540/1540
```

No changed-answer judge is needed.

## Decision

Promote v267 to local LTS.

Rationale: v267 reduces build-system risk without changing performance. Typed memory is now explicitly audited as a source-backed activation hint, while raw source rows remain the final-answer evidence authority.

## Outputs

```text
outputs/diagnostic/stage1_memory_governance_v267_lme_full/predictions.jsonl
outputs/diagnostic/stage1_memory_governance_v267_lme_full/traces.jsonl
outputs/diagnostic/stage1_memory_governance_v267_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_memory_governance_v267_locomo_full/traces.jsonl
experiments/diagnostic/stage1_memory_governance_v267_lme_full/
experiments/diagnostic/stage1_memory_governance_v267_locomo_full/
```

## Next Steps

1. Use governance flags to guide a real build-time improvement: validity/confidence calibration and source span completeness before retrieval consumes the signals.
2. Keep activation use conservative: source-backed, confidence-aware, and always resolving final evidence to raw rows.
3. Continue simplifying query-time compatibility layers after build governance is stable.
