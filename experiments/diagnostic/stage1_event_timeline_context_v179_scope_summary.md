# V179 Source Event Timeline Context Rejected

## Decision

Do not promote v179. Current LTS remains v176.

v179 is a clean compiler-side context organization attempt: it adds a
source-backed `Source Event Timeline` block for explicit chronological/order
questions and separates exact event dates from vague `recently`-style relative
time. The idea is methodologically useful, but this implementation is too
intrusive in the answer prompt and hurts changed-answer judge accuracy.

## Method

- Parent LTS: v176 (`b38e6ad`).
- Algorithm commit: `052b564`.
- Config:
  `configs/stage1_event_timeline_context_v179_qwen36_no_think_build4k_cached.json`.
- Change:
  - add `compiler.event_timeline`;
  - only applies to explicit chronological/order questions in
    `current_state`, `list_count`, or `temporal_lookup`;
  - emits a compact row index with `time_kind` values:
    `exact_today`, `explicit_date`, `relative_phrase`,
    `vague_relative_recent`, or `mention_time_only`;
  - marks vague `recently` as low precision and not a strict before/after fact.

The block uses only visible Memory Context rows, row timestamps, question text
and deterministic text normalization. It does not use gold answers, judge
outputs, benchmark labels, sample ids, test feedback or sample-level rules.

## Probe Result

The same 4 LongMemEval order/timeline rows identified during v178 trigger
analysis were used as a clean probe.

| Item | Result |
|---|---:|
| probe samples | `4` |
| answer cache | `0` hits, `4` misses, `4` writes |
| repair triggered | `0` |
| avg query tokens | `9995.0` on the 4-row probe |
| avg context chars | `25388.0` |
| answer diff vs v176 | `3/4` |

Changed-answer paired dual `deepseek-v4-flash` judge on the 3 changed answers:

| Metric | v176 | v179 |
|---|---:|---:|
| strict correct | `1/3` | `0/3` |
| lenient correct | `1/3` | `0/3` |
| strict delta | - | `-1` |
| lenient delta | - | `-1` |

Because the changed-answer judge is negative, no full LME or LoCoMo run was
performed.

## Badcase Pattern

The timeline block made the answerer over-trust the derived ordering index. It
changed one previously correct temporal-order answer into a wrong order, and it
also produced low-quality outputs in other changed rows, including a partial
meta answer and a duplicated airline list. This means the timeline as currently
inserted competes with raw Memory Context rather than merely organizing it.

## Next Step

- Do not inject a broad event timeline block directly into the answer prompt.
- Keep the useful design idea, but move it toward a stricter typed event-time
  table or diagnostic candidate map with explicit inclusion gates.
- If revisiting this direction, require the candidate map to be answer-slot
  aware, deduplicate entities before ordering, and avoid emitting a tentative
  final order unless all in-scope items have high-confidence event times.

## Artifacts

- Probe run:
  `experiments/diagnostic/stage1_event_timeline_context_v179_trigger_probe/`
- Changed-answer judge:
  `experiments/diagnostic/stage1_event_timeline_context_v179_changed_vs_v176/`
- Probe predictions/traces:
  `outputs/diagnostic/stage1_event_timeline_context_v179_trigger_probe/`
- Changed subset:
  `outputs/diagnostic/stage1_event_timeline_context_v179_changed_vs_v176/`
