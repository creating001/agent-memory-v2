# stage1_candidate_evidence_map_v192 diagnostic summary

## Decision

V192 is rejected and does not replace the v191 LTS.

V192 adds a narrow `Candidate Evidence Map` for `temporal_lookup` and `list_count` questions while preserving v191 retrieval, raw row budget, Event-Time Candidate Map gates, weekend parser gating, answer, repair, and clean constraints. The intent was coverage-preserving context organization for #2/#5 risk: add a compact source index without pruning raw evidence or treating the index as independent evidence.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, query-time route, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, or cache construction.
- The changed-answer dual judge below is offline evaluation only.

## Probe Result

Activation probe:

| Item | v191 | v192 |
|---|---:|---:|
| answer diff vs v191 | - | `2/3` |
| avg query tokens | `5578.667` | `6244.333` |
| avg context chars | `15927.333` | `17977.000` |
| answer cache | `3/0/0` | `0/3/3` |

Changed-answer dual `deepseek-v4-flash` judge on the two rows where v192 changed v191:

| Version | strict | lenient |
|---|---:|---:|
| v191 | `2/2` | `2/2` |
| v192 | `1/2` | `1/2` |

The negative row is `acae332af0e2a71091b4c697`:

- Question: `When did Nate take time off to chill with his pets?`
- v191: `2022-08-22`，dual judge `CORRECT/CORRECT`
- v192: `The weekend of August 27-28, 2022`，dual judge `WRONG/WRONG`

## Diagnosis

The generic Candidate Evidence Map is still too strong for temporal questions. On the Nate row it highlights the selected turn text containing `this weekend`, which causes the answer model to prefer the weekend span over v191's mention-date answer. This increases prompt length and loses the v184/v191 LoCoMo positive changed-answer result.

This does not mean context organization is the wrong direction. It means a broad visible candidate guide is unsafe for temporal lookup unless it can separate `mention_time`, event-relative phrases, selected-context wrappers, and question-slot coverage more precisely.

## Artifacts

- Config: `configs/stage1_candidate_evidence_map_v192_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `19cd7a5f9cf364b094db2a32530e97d577b9ac7c`
- Activation probe: `experiments/diagnostic/stage1_candidate_evidence_map_v192_activation_probe/`
- Predictions: `outputs/diagnostic/stage1_candidate_evidence_map_v192_activation_probe/predictions.jsonl`
- Traces: `outputs/diagnostic/stage1_candidate_evidence_map_v192_activation_probe/traces.jsonl`
- Changed-answer judge: `outputs/diagnostic/stage1_candidate_evidence_map_v192_changed_vs_v191_probe/`

## Next

- Do not expand broad Candidate Evidence Map to full evaluation.
- Continue from v191 LTS.
- Next attempt should keep typed/source-backed activation, but make temporal context organization conflict-aware rather than simply adding a visible ranked candidate list.
