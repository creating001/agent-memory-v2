# V181 Grouped Event-Time Candidate Manifest LTS

## Decision

Promote v181 to the current local LTS.

v181 inherits v180 and keeps event-time candidates trace-only, then adds a
grouped answer-slot management view in `compiled_context.diagnostics`. The new
view reduces #5 memory organization/conflict audit risk by grouping candidate
event times per dedup slot and recording source ids, high-confidence source ids,
time kinds, conflict type, best candidate, and resolution state.

The grouped view is not included in the answer prompt, retrieval, repair,
finalizer, cache keys, or judge.

## Method

- Parent LTS: v180 (`ac35180`).
- Algorithm commit: `e1bd788`.
- Config:
  `configs/stage1_grouped_event_time_candidate_manifest_v181_qwen36_no_think_build4k_cached.json`.
- Added trace fields:
  - `candidate_groups`;
  - `grouped_view`;
  - `candidate_group_count`;
  - per-group `source_ids`, `high_confidence_source_ids`, `event_times`,
    `time_kinds`, `best_source_id`, `best_event_time`, `conflict_type`, and
    `resolution`.

The method uses only visible question text, route, source-linked Memory Context
rows, row timestamps, and deterministic date parsing. It uses no gold answers,
judge output, benchmark labels, sample ids, test feedback, or sample-level
rules.

## Full Validation

| Benchmark | Answer diff vs v180 | Cache | Grouped manifest coverage | Performance |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | answer `500/500` hits | manifest `234/500`; avg groups `7.363`; avg conflict groups `1.286`; safe order `0` | inherits v180/v176: strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | answer `1540/1540` hits | manifest `356/1540`; avg groups `6.753`; avg conflict groups `1.761`; safe order `2` | inherits v180/v176: strict/lenient `0.792857 / 0.818182` |

No changed-answer judge was needed because predictions are identical to v180 on
both full sets. Query token averages are unchanged: LME `6291.590`, LoCoMo
`6064.337`.

LoCoMo's run manifest records `dirty=true` because the LME v181 experiment
directory was untracked while LoCoMo was running. This is a bookkeeping artifact,
not a prediction-path difference; it is recorded rather than rerun only for a
clean manifest.

## Risk Impact

- #5 memory lifecycle/state/conflict/query-time reasoning: reduced. v181 turns
  the flat event-time manifest into an auditable grouped management view, so the
  next prompt-safe candidate-map design can reason over slot conflicts instead
  of raw candidate rows.
- #2 token/context risk: unchanged. The prompt and answer cache are unchanged;
  no extra query tokens are introduced.
- #4 finalizer/verifier risk: unchanged. v181 does not add answer-time repair or
  finalization.
- #1 granularity/profile and #3 selected-context risks remain open.

## Next Step

Use v181 `candidate_groups` to design a narrow prompt-safe candidate map only
for groups with high-confidence source-backed candidates and no event-time
conflict. Do not expose low-precision or conflicted groups to the answer prompt
until a small changed-answer probe shows benefit.

## Artifacts

- LME run:
  `experiments/diagnostic/stage1_grouped_event_time_candidate_manifest_v181_lme_s_full/`
- LoCoMo run:
  `experiments/diagnostic/stage1_grouped_event_time_candidate_manifest_v181_locomo_nonadv_full/`
- Full predictions/traces:
  - `outputs/diagnostic/stage1_grouped_event_time_candidate_manifest_v181_lme_s_full/`
  - `outputs/diagnostic/stage1_grouped_event_time_candidate_manifest_v181_locomo_nonadv_full/`
