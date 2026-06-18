# stage1_build_memory_usage_trace_audit_v126_plan

## Purpose

Diagnose whether build-stage typed memory is currently unused, or whether it is used mainly as a source projection index without enough organization, conflict handling, and query-time reasoning support.

This audit reads only completed prediction-time traces. It does not read gold answers, judge outputs, benchmark labels, sample ids, row indices, or test feedback.

## Inputs

- LME traces: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792/traces.jsonl`
- LoCoMo traces: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/traces.jsonl`

## External Method Framing

The relevant method notes point to the same constraint:

- Graphiti / temporal KG: derived facts and edges must retain raw episode/message backpointers and valid-time metadata.
- MemOS / memory OS designs: memory is a lifecycle-managed resource, but recall must still expose provenance.
- MemMachine / episode memory: retrieve a nucleus raw episode/turn and expand grounded neighborhood, instead of answering from profile memory alone.
- SimpleMem / typed memory: compression and typed facts can improve density, but raw dialogue must remain the final evidence layer.

For this project, build memory should therefore become a source-backed organization and selection signal, not an independent answer source and not another large reader prompt block.

## Trace Findings

### LongMemEval-S V116

| metric | value |
|---|---:|
| samples | `500` |
| samples with memory hits | `489 / 500 = 0.978` |
| samples with memory-projected source in final rows | `486 / 500 = 0.972` |
| avg memory hits | `8.424` |
| avg memory source hits | `9.684` |
| avg final evidence rows | `34.752` |
| avg memory source ids in final rows | `6.358` |

By route:

| route | n | avg memory hits | avg memory source hits | avg memory sources in final rows |
|---|---:|---:|---:|---:|
| `current_state` | `22` | `8.23` | `9.95` | `6.50` |
| `fact_lookup` | `183` | `7.43` | `8.80` | `5.75` |
| `list_count` | `119` | `9.03` | `10.00` | `6.27` |
| `profile_preference` | `15` | `5.20` | `6.40` | `4.07` |
| `temporal_lookup` | `161` | `9.44` | `10.72` | `7.31` |

### LoCoMo V116

| metric | value |
|---|---:|
| samples | `1540` |
| samples with memory hits | `1539 / 1540 = 0.999` |
| samples with memory-projected source in final rows | `1539 / 1540 = 0.999` |
| avg memory hits | `19.858` |
| avg memory source hits | `25.938` |
| avg final evidence rows | `54.144` |
| avg memory source ids in final rows | `11.582` |

By route:

| route | n | avg memory hits | avg memory source hits | avg memory sources in final rows |
|---|---:|---:|---:|---:|
| `current_state` | `4` | `20.00` | `28.75` | `12.25` |
| `fact_lookup` | `882` | `19.81` | `26.03` | `11.63` |
| `list_count` | `270` | `19.88` | `26.12` | `11.85` |
| `profile_preference` | `46` | `20.00` | `26.22` | `12.74` |
| `temporal_lookup` | `338` | `19.95` | `25.48` | `11.07` |

## Diagnosis

Build memory is already active as a source projection index. The weakness is not that no memory records are retrieved; it is that the records do not yet manage the final evidence set as typed coverage, conflict/state chains, or entity/session clusters.

Earlier diagnostics support this:

- V118/V119 reader-side source manifests and inline memory hints were clean but negative; adding memory text to the reader prompt increased noise.
- V120 rerank tail filtering reduced tokens but hurt list/count coverage; coverage matters more than compressing broad evidence.
- V125 temporal local evidence unit helped the source expansion direction without exposing derived memory as evidence.

## V126 Candidate Direction

Do not add another reader prompt block.

The next candidate should use build memory before the final prompt, as a source-backed organization layer:

- group raw evidence rows by source-linked memory records, entities, memory type, and temporal fields
- identify coverage gaps such as retrieved typed memory whose raw source is outside the final row budget
- for `temporal_lookup` and `current_state`, prefer small conflict/update chains over unrelated same-entity rows
- for `list_count`, avoid cutting broad evidence; use memory only to deduplicate or diversify source groups
- keep all final answer evidence as raw Memory Context rows

Potential low-risk implementation path:

1. Add a dry-run-only trace analyzer for `memory_source_coverage`: memory hits, source ids, final-row inclusion, memory type coverage, superseded/current status coverage.
2. Add a configurable retrieval/compiler ordering candidate such as `memory_source_cluster_coverage`, initially route-scoped and dry-run only.
3. Compare context churn and final row ids before running answer LLM.

This follows Graphiti/MemOS/MemMachine/SimpleMem at the level that matters here: typed memory manages source-backed evidence selection, not answer generation.
