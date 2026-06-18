# V144 Memory Version Chain Scope Summary

## Purpose

V144 targets goal risk #5 in the broader sense: memory lifecycle, source-backed state/version organization, conflict handling, and query-time memory reasoning. It is not another typed-memory-as-evidence prompt guide.

The algorithm commit is `5d42ab6 feat: add v144 memory version chain ordering`.

## External Method References

- Graphiti/Zep: temporal fact validity windows, invalidating old facts without deleting them, and provenance from derived facts back to raw episodes: https://github.com/getzep/graphiti
- LangMem: memory update as conversation plus current memory state to updated memory state, with semantic/episodic/procedural separation: https://langchain-ai.github.io/langmem/concepts/conceptual_guide/
- Mem0: multi-signal retrieval from semantic, BM25, and entity matching, with temporal reasoning over current/past state: https://github.com/mem0ai/mem0
- MemOS/OpenMemory: inspectable/editable memory and explainable recall traces rather than black-box embedding-only stores: https://github.com/MemTensor/MemOS and https://github.com/CaviraOSS/OpenMemory

Adopted idea: use typed memory only as a source-backed version/provenance signal to organize raw evidence rows. Rejected for now: large memory OS, graph database dependency, direct typed-memory answer evidence, and broad prompt guide sections.

## Mechanism

`memory_version_chain_interleave` groups visible source rows from typed memory records that share `(memory_type, subject, predicate)` and have multiple values or superseded records. For `profile_preference` and `current_state`, it keeps retrieval anchors, then moves active/superseded raw source rows together. The final answer still sees raw Memory Context rows; `compiler.max_memory_records` remains `0`.

Clean boundary:
- no gold/reference answers;
- no judge outputs;
- no benchmark labels/categories;
- no sample ids, qids, or row indices;
- no test feedback or sample-level rules.

## Compile-Only Scope

These runs used a temporary `/tmp` null-answer config. They do not measure accuracy.

| Benchmark | run | changed prompts | changed rows | avg context chars |
|---|---|---:|---:|---:|
| LongMemEval-S full | `stage1_memory_version_chain_v144_lme_s_full_compile` | `31/500` | `31/500` | `19775.406` |
| LoCoMo non-adversarial full | `stage1_memory_version_chain_v144_locomo_nonadv_full_compile` | `50/1540` | `50/1540` | `17400.688` |

Compared with fresh v127:
- LME changed prompts are `17 current_state` and `14 profile_preference`; total context delta is `+2898` chars, about `+5.796` chars/sample.
- LoCoMo changed prompts are `4 current_state` and `46 profile_preference`; total context delta is `+72` chars, about `+0.047` chars/sample.
- No `memory_state_guide` prompt section is enabled.

## Decision

Proceeding to formal was justified by the narrow compile scope. The formal result rejects v144 as a unified LTS:

| Benchmark | strict | lenient | LTS decision |
|---|---:|---:|---|
| LongMemEval-S full | `406/500 = 0.812000` | `420/500 = 0.840000` | mixed vs fresh v127 `410/500` strict and `416/500` lenient |
| LoCoMo non-adversarial full | `1210/1540 = 0.785714` | `1250/1540 = 0.811688` | below fresh v127 `1216/1540` strict and `1256/1540` lenient |

Paired changed-prompt subset vs fresh v127:
- LME strict net `-2`, lenient net `0`.
- LoCoMo strict net `+1`, lenient net `0`.

Conclusion: v144 is cleaner than v142's prompt guide for risk #5 because it keeps typed memory out of direct reader evidence, but row reordering alone does not improve accuracy enough. Keep v127 as current LTS and keep v144 as a reusable ablation for future state/version retrieval work.

## Outputs

- LME compile traces: `outputs/diagnostic/stage1_memory_version_chain_v144_lme_s_full_compile/traces.jsonl`
- LME compile experiment record: `experiments/diagnostic/stage1_memory_version_chain_v144_lme_s_full_compile/`
- LME formal judge: `experiments/formal/stage1_memory_version_chain_v144_lme_s_full/deepseek_dual_judge.json`
- LoCoMo compile traces: `outputs/diagnostic/stage1_memory_version_chain_v144_locomo_nonadv_full_compile/traces.jsonl`
- LoCoMo compile experiment record: `experiments/diagnostic/stage1_memory_version_chain_v144_locomo_nonadv_full_compile/`
- LoCoMo formal judge: `experiments/formal/stage1_memory_version_chain_v144_locomo_nonadv_full/deepseek_dual_judge.json`
