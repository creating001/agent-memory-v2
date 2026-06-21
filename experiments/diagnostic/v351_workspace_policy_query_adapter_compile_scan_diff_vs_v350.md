# v351 workspace policy query adapter compile-scan diff vs v350

## Purpose

v351 tests whether build-owned `memory_workspace_policy.query_component_policy` can take over the guide replacement that v350 still encoded as hand-written compiler route overrides. It keeps v350's `inline_spaced` raw Memory Context header compression, but the current/fact/profile query surface is now gated by:

- `memory_workspace_policy.applied`
- ready `query_component_policy` entries
- a source-backed Working Memory Packet grounded in visible raw Memory rows

If any gate fails, legacy guide blocks remain. Derived memory remains an activation/index surface only; final evidence remains raw Memory Context rows.

## Clean Boundary

This is a clean compile-scan diagnostic. Prediction code does not use labels, judge outputs, gold answers, benchmark tags, sample ids, test feedback, or sample-level rules. `record_key` is used only offline to align trace files.

## Runs

| Benchmark | v350 baseline traces | v351 traces |
|---|---|---|
| LongMemEval-S probe50 | `outputs/diagnostic/v350_inline_spaced_memory_context_compile_scan_lme_probe50/traces.jsonl` | `outputs/diagnostic/v351_workspace_policy_query_adapter_compile_scan_lme_probe50/traces.jsonl` |
| LoCoMo non-adversarial probe50 | `outputs/diagnostic/v350_inline_spaced_memory_context_compile_scan_locomo_probe50/traces.jsonl` | `outputs/diagnostic/v351_workspace_policy_query_adapter_compile_scan_locomo_probe50/traces.jsonl` |

## Diff Summary

| Benchmark | n | row set diff | row order diff | prompt diff | avg prompt char delta | workspace policy applied | not applied reasons |
|---|---:|---:|---:|---:|---:|---:|---|
| LongMemEval-S probe50 | 50 | 0 | 0 | 0 | `0.00` | 33 | `route_not_enabled=17` |
| LoCoMo non-adversarial probe50 | 50 | 0 | 0 | 0 | `0.00` | 18 | `route_not_enabled=32` |

Block counts were unchanged from v350:

| Benchmark | Structured Guide | Working Memory Packet |
|---|---:|---:|
| LongMemEval-S probe50 | 17 | 33 |
| LoCoMo non-adversarial probe50 | 33 | 17 |

Applied replacement counts:

| Benchmark | structured guide | memory state guide | memory value slot guide |
|---|---:|---:|---:|
| LongMemEval-S probe50 | 33 | 33 | 33 |
| LoCoMo non-adversarial probe50 | 18 | 18 | 18 |

## Interpretation

v351 is behavior-preserving relative to v350 on both probe50 compile scans: same raw rows, same row order, same prompt text. The improvement is architectural rather than prompt-surface: the query-time guide replacement is now controlled by build-owned workspace readiness and source-backed packet availability instead of static route overrides.

Because the compiled prompts are identical to v350 on this probe, no answer or judge rerun was done for v351. The relevant query-token baseline remains v350's answer probe: LongMemEval-S avg query tokens `5202.84`, LoCoMo avg query tokens `5331.48`. A larger/full cache-aligned diff is still required before treating v351 as LTS.

## Decision

Keep v351 as the current clean system-architecture candidate. It reduces the "query stage is too manually wired / benchmark-shaped" risk while preserving v350's query-token surface on probe50. Do not promote to LTS yet without larger/full diff coverage.
