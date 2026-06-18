# V145 Memory Slot Chain Scope Summary

## Purpose

V145 continues risk #5 beyond evidence ordering. It moves source-backed state/version handling into retrieval-time candidate expansion: when build-memory BM25 activates a stateful slot, the pipeline also adds raw source rows from the same active/superseded `(memory_type, subject, predicate)` chain.

The algorithm commit is `845c6a4 feat: add v145 memory slot chain retrieval`.

## Mechanism

`retrieval.memory_slot_chain` is enabled only for `profile_preference` and `current_state`. It reads build-stage typed memory records and their raw `source_ids`, but it does not expose typed memory text as independent reader evidence. `compiler.max_memory_records` remains `0`; final answers still see raw Memory Context rows.

V145 also keeps v144 `memory_version_chain_interleave` for final source-backed row organization in those two routes.

Clean boundary:
- no gold/reference answers;
- no judge outputs;
- no benchmark labels/categories;
- no sample ids, qids, or row indices;
- no test feedback or sample-level rules.

## Compile-Only Scope

These runs used a temporary `/tmp` null-answer config. They do not measure accuracy.

| Benchmark | run | slot-chain applied | slot source hits | changed prompts vs v127 | row-set changes vs v127 | avg context chars |
|---|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `stage1_memory_slot_chain_v145_lme_s_full_compile` | `16/500` | `76` | `31/500` | `15/500` | `19767.300` |
| LoCoMo non-adversarial full | `stage1_memory_slot_chain_v145_locomo_nonadv_full_compile` | `34/1540` | `177` | `50/1540` | `29/1540` | `17400.706` |

Compared with fresh v127:
- LME total context delta is `-1155` chars, about `-2.310` chars/sample.
- LoCoMo total context delta is `+99` chars, about `+0.064` chars/sample.
- Slot-chain triggers only on `current_state` / `profile_preference`; fact/list/temporal routes are unchanged.

Compared with v144 compile:
- LME adds `11/500` prompt/order changes and `9/500` row-set changes.
- LoCoMo adds `29/1540` prompt/order changes and `29/1540` row-set changes.

## Decision

Compile scope is narrow and cost-neutral enough to proceed to formal answer + dual `deepseek-v4-flash` judge. Do not promote before full judge accuracy is available.

## Outputs

- LME compile traces: `outputs/diagnostic/stage1_memory_slot_chain_v145_lme_s_full_compile/traces.jsonl`
- LME compile experiment record: `experiments/diagnostic/stage1_memory_slot_chain_v145_lme_s_full_compile/`
- LoCoMo compile traces: `outputs/diagnostic/stage1_memory_slot_chain_v145_locomo_nonadv_full_compile/traces.jsonl`
- LoCoMo compile experiment record: `experiments/diagnostic/stage1_memory_slot_chain_v145_locomo_nonadv_full_compile/`
