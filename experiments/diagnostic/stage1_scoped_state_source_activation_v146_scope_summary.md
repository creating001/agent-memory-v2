# V146 Scoped State Source Activation Summary

## Purpose

V146 tightens the failed v145 retrieval-time slot-chain idea for risk #5.
It keeps the v127 LTS retrieval/compiler/answer base and uses typed memory only
as source-backed activation over raw rows:

- no typed memory text is exposed as reader evidence;
- `compiler.max_memory_records` remains `0`;
- slot-chain expansion is limited to `current_state` / `profile_preference`;
- the question must have an explicit lifecycle scope;
- the activated active/superseded record must overlap the question through
  predicate/value/text terms beyond subject/person and generic scope words.

This targets the user's risk #5 clarification: memory may activate raw sources,
but final evidence must remain evidence-first and source-faithful.

Clean boundary:
- no gold/reference answers;
- no judge outputs;
- no benchmark labels/categories;
- no sample ids, qids, or row indices;
- no test feedback or sample-level rules.

## Compile-Only Scope

These runs used a temporary `/tmp` null-answer config. They do not measure
accuracy.

| Benchmark | run | slot-chain applied | slot source hits | changed prompts vs v127 | row-set changes vs v127 | avg context chars |
|---|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `stage1_scoped_state_source_activation_v146_lme_s_full_compile` | `1/500` | `2` | `0/500` | `0/500` | `19769.610` |
| LoCoMo non-adversarial full | `stage1_scoped_state_source_activation_v146_locomo_nonadv_full_compile` | `0/1540` | `0` | `0/1540` | `0/1540` | `17400.642` |

Compared with v145, the scope gate removes the noisy state/profile expansions:

| Benchmark | v145 slot-chain applied | v146 slot-chain applied | v145 row-set changes vs v127 | v146 row-set changes vs v127 |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `16/500` | `1/500` | `15/500` | `0/500` |
| LoCoMo non-adversarial full | `34/1540` | `0/1540` | `29/1540` | `0/1540` |

## Decision

Do not run formal judge and do not promote to LTS.

Reason: v146 is cleaner and safer than v145 for risk #5, but after the
slot-overlap guard it is effectively a no-op relative to v127 on both full
benchmarks. Since it changes no final prompt or evidence row set, full judge
would duplicate v127 predictions and add cost without useful information.

Keep v127 as current LTS. The next #5 attempt should not rely on same-slot
source expansion alone; it needs a more useful query-time state model, such as
explicit as-of/current/historical state interpretation, conflict-chain pruning,
and answer-slot-aware source selection over raw evidence.

## Outputs

- LME compile traces: `outputs/diagnostic/stage1_scoped_state_source_activation_v146_lme_s_full_compile/traces.jsonl`
- LME compile experiment record: `experiments/diagnostic/stage1_scoped_state_source_activation_v146_lme_s_full_compile/`
- LoCoMo compile traces: `outputs/diagnostic/stage1_scoped_state_source_activation_v146_locomo_nonadv_full_compile/traces.jsonl`
- LoCoMo compile experiment record: `experiments/diagnostic/stage1_scoped_state_source_activation_v146_locomo_nonadv_full_compile/`
