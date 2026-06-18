# V178 Source-Grounded Temporal Order Repair Rejected

## Decision

Do not promote v178. Current LTS remains v176.

v178 is a clean, opt-in verifier for chronological/order questions. The trigger
is narrow, but the probe produced no answer changes and added repair-token cost.
It therefore does not improve performance or reduce enough risk relative to
v176.

## Method

- Parent LTS: v176 (`b38e6ad`).
- Algorithm commit: `2353bdf`.
- Config:
  `configs/stage1_source_grounded_temporal_order_repair_v178_qwen36_no_think_build4k_cached.json`.
- Change:
  - add `enable_source_grounded_temporal_order_trigger`;
  - trigger only when the question explicitly asks for chronological/order
    sequencing;
  - require draft JSON `answer_type` in `order/list`;
  - require at least three source-backed support items with event dates in
    prediction-time `evidence_report`;
  - verifier may reorder only by source-backed event time from Memory Context
    and Draft Answer JSON.

The prediction path uses only question text, route, draft JSON, visible Memory
Context and source-backed `evidence_report`. It does not use gold answers, judge
outputs, benchmark labels, sample ids, test feedback or sample-level rules.

## Probe Result

Before running new model calls, the new trigger was simulated over existing
v176 full traces:

| Scope | Triggered |
|---|---:|
| LongMemEval-S full | `4/500` |
| LoCoMo non-adversarial full | `0/1540` |

Then a clean 4-row LongMemEval probe was run on those triggered inputs:

| Item | Result |
|---|---:|
| answer cache | `4` hits, `0` misses |
| repair triggered | `4/4` |
| repair applied | `0/4` |
| repair cache | `0` hits, `4` misses, `4` writes |
| repair query tokens | `27233` total, `6808.25` avg when triggered |
| answer diff vs v176 | `0/4` |

No changed-answer judge was run because the changed-answer set is empty. Full
LME/LoCoMo runs were not run because the probe already shows no accuracy-change
surface while adding repair calls.

## Badcase Lesson

The main tempting LME badcase asks for the order of six museums from earliest to
latest. v176 answers with Museum of Contemporary Art before Science Museum. The
visible prediction-time evidence report says the Museum of Contemporary Art
lecture series was `before 2023-01-15`, while Science Museum is on
`2023-01-15`. The v178 verifier therefore keeps MoCA first under the
source-grounded rules.

Forcing Science Museum before MoCA would require privileging the offline gold
ordering over the visible Memory Context interpretation of `recently`, which is
not clean. This is the right place to stop: the problem is not that the verifier
needs a stronger benchmark-specific rule, but that the memory/compiler should
represent relative event times, precision and uncertainty more explicitly.

## Next Step

- Do not add a temporal-order verifier that overrides source-backed relative
  time interpretation just to match a benchmark gold ordering.
- For #5, move the next attempt toward a source-backed event timeline table:
  item/event, source row, event_time, time_precision, relative anchor, and
  conflict/uncertainty status.
- For #2/#3, keep avoiding broad selected-context expansion; the next useful
  direction is compact context organization, not more raw neighbor injection.

## Artifacts

- Probe run:
  `experiments/diagnostic/stage1_source_grounded_temporal_order_repair_v178_trigger_probe/`
- Probe predictions/traces:
  `outputs/diagnostic/stage1_source_grounded_temporal_order_repair_v178_trigger_probe/`
