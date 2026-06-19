# stage1_build_memory_object_graph_v248_probe_summary

## Purpose

Validate v248 as a trace-only build-stage system layer on top of the v235 LTS prediction path.

v248 adds `build_memory.management.object_graph`, a source-backed object/slot graph over typed memory records. It groups records by `memory_type + subject + predicate`, separates managed lifecycle slots from collection multi-value slots, records conflict/multi-value/source coverage counts, and keeps bounded representative active/superseded values and source ids.

## Setup

- Config: `configs/stage1_build_memory_object_graph_v248_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `130ef828a22d2290e662073b31cfc7e6a546916e`
- Prediction path: v235 LTS retrieval/compiler/answer/repair/finalizer/cache namespaces unchanged.
- Clean setting: object graph is built only from source-backed typed memory records derived from raw turns; it is not used by retrieval, compiler, answer, repair, finalizer, or cache keys.

## Probe Results

| Benchmark | n | answer diff vs v235 | query-token diff rows | retrieval-order diff rows | avg query tokens | object graph coverage |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | 50 | 0 | 0 | 0 | `5677.40` | `50/50`, avg slots `90.74` |
| LoCoMo non-adv | 50 | 0 | 0 | 0 | `6543.56` | `50/50`, avg slots `85.00` |

No judge was run because predictions were answer-identical to v235 on both probes.

## Diagnosis

This is a safe build-stage systemization step. It does not improve accuracy by itself, but it reduces method risk by making the build memory layer less like a flat typed-record list and more like an auditable memory system. The graph exposes lifecycle vs collection slots and source coverage, which should guide later compiler/verifier work without repeating the v246/v247 mistake of deleting retrieval evidence.

## Decision

Keep v248 as a full-candidate trace-only LTS step. Before replacing v235, run full answer/retrieval diff on LongMemEval-S and LoCoMo. If full diff remains zero, v248 can inherit v235 accuracy while reducing build-stage observability risk.

## Outputs

- LME probe: `outputs/diagnostic/stage1_build_memory_object_graph_v248_lme_probe50/`
- LoCoMo probe: `outputs/diagnostic/stage1_build_memory_object_graph_v248_locomo_probe50/`
