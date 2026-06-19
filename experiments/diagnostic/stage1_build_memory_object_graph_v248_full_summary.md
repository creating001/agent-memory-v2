# stage1_build_memory_object_graph_v248_full_summary

## Purpose

Promote v248 from full candidate to LTS if the trace-only build memory object graph does not change prediction behavior on LongMemEval-S full or LoCoMo non-adversarial full.

## Setup

- Config: `configs/stage1_build_memory_object_graph_v248_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `130ef828a22d2290e662073b31cfc7e6a546916e`
- Probe evidence commit: `8392df2ecfe73e22b8085f37761f5e8d9960026d`
- Prediction path: v235 LTS retrieval/compiler/answer/repair/finalizer/cache namespaces unchanged.
- Clean setting: object graph is trace-only and built only from source-backed typed memory records derived from raw turns.

## Full Diff

| Benchmark | n | answer diff vs v235 | query-token diff rows | retrieval-order diff rows | object graph coverage |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | 500 | 0 | 0 | 0 | `500/500`, avg slots `89.26`, max `126` |
| LoCoMo non-adv | 1540 | 0 | 0 | 0 | `1540/1540`, avg slots `127.70`, max `153` |

No judge was rerun because predictions are answer-identical to v235 on both full benchmarks. v248 inherits v235 dual DeepSeek flash judge accuracy:

| Benchmark | strict/lenient | counts | avg build/query tokens |
|---|---:|---:|---:|
| LongMemEval-S full | `0.832000 / 0.844000` | `416/500`, `422/500` | `85393.566 / 6579.782` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `1223/1540`, `1262/1540` | `62015.57402597403 / 6094.017532467533` |

LoCoMo full manifest has `dirty=true` only because the LME full experiment directory was untracked when LoCoMo started; source/config code was already committed at `8392df2`.

## Diagnosis

v248 reduces build-stage system risk without trading away accuracy. The build memory layer is no longer only a flat typed record list in the trace: it exposes source-backed subject/predicate slots, lifecycle vs collection distinctions, conflict counts, multi-value active slots, source coverage, and representative active/superseded values.

This addresses the new goal's build-side weakness while avoiding the v246/v247 failure mode. The graph does not delete or reorder retrieval hits and does not enter prompts, so it is a safer base for later compiler/verifier improvements.

## Decision

Promote v248 to current local LTS. It inherits v235 performance and token costs, while improving build-stage observability and general system structure in a clean, source-backed, benchmark-agnostic way.

## Outputs

- LME full: `outputs/diagnostic/stage1_build_memory_object_graph_v248_lme_full/`
- LoCoMo full: `outputs/diagnostic/stage1_build_memory_object_graph_v248_locomo_full/`
