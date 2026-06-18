# V180 Trace Event-Time Candidate Manifest LTS

## Decision

Promote v180 to the current local LTS.

v180 inherits v176 and adds a trace-only answer-slot-aware event-time candidate
manifest. It reduces #5 lifecycle/query-time organization audit risk after v179
showed that injecting a timeline block into the answer prompt is too intrusive.
The manifest is written only to `compiled_context.diagnostics`; it is not used
by retrieval, answer prompt, repair, finalizer, cache keys, or judge.

## Method

- Parent LTS: v176 (`b38e6ad`).
- Algorithm commit: `2146e7a`.
- Config:
  `configs/stage1_trace_event_time_candidate_manifest_v180_qwen36_no_think_build4k_cached.json`.
- Trace fields:
  - source-backed `event_time` vs `mention_time`;
  - `time_kind` and precision rank;
  - answer-slot `dedup_key`;
  - conflict groups;
  - `safe_order_source_ids` only when all selected slots have high-precision
    event times and no dedup/time conflict.

The method uses only visible question text, route, source-linked Memory Context
rows, row timestamps, and deterministic date parsing. It uses no gold answers,
judge output, benchmark labels, sample ids, test feedback, or sample-level
rules.

## Full Validation

| Benchmark | Answer diff vs v176 | Cache | Manifest coverage | Performance |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | answer `500/500` hits | `234/500`, safe order `0` | inherits v176: strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | answer `1540/1540` hits | `356/1540`, safe order `2` | inherits v176: strict/lenient `0.792857 / 0.818182` |

No changed-answer judge was needed because predictions are identical to v176 on
both full sets. Query token averages also inherit v176: LME `6291.590`, LoCoMo
`6064.337`.

## Risk Impact

- #5 event/state/time organization: reduced. The system now records
  source-backed candidate event-time slots, dedup keys, precision, and conflict
  reasons without asking the answer model to trust a derived timeline.
- #4 clean verifier/finalizer risk: unchanged. v180 does not add answer-time
  repair or finalization.
- #2 token/context risk: unchanged. The prompt and answer cache are unchanged;
  query-token averages do not increase.
- #1 granularity/profile and #3 selected-context risks remain open.

## Next Step

Use the v180 manifest buckets to inspect where event-time candidates are blocked
by dedup/time conflicts, then design a narrower prompt-safe organization module.
Do not emit a prompt timeline unless the manifest shows high-confidence,
distinct answer slots and the intervention has a changed-answer judge benefit.

## Artifacts

- LME run:
  `experiments/diagnostic/stage1_trace_event_time_candidate_manifest_v180_lme_s_full/`
- LoCoMo run:
  `experiments/diagnostic/stage1_trace_event_time_candidate_manifest_v180_locomo_nonadv_full/`
- Full predictions/traces:
  - `outputs/diagnostic/stage1_trace_event_time_candidate_manifest_v180_lme_s_full/`
  - `outputs/diagnostic/stage1_trace_event_time_candidate_manifest_v180_locomo_nonadv_full/`
