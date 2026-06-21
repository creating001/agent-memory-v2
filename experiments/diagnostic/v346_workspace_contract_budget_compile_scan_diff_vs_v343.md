# v346 Workspace Contract Budget Compile-Scan Diff vs v343

## Purpose

Test whether the build-owned `memory_workspace_contract_v1` can safely participate in runtime context budgeting before changing answer behavior. v346 inherits v343 guard-only source-backed slot coverage and changes only `retrieval.context_budget` / `context_budget_audit`:

- `registry_anchor_retention=true`
- `anchor_source=memory_workspace_contract`
- v343 context budget remains `max_hits=60`, `max_chars=22000`, `min_hits=32`, `protect_top_n=32`
- compiler evidence limits, guides, raw Memory rows, answer rules, and null-answer compile-scan mode stay unchanged

This is a clean diagnostic. The prediction pipeline does not use labels, judge outputs, gold answers, benchmark tags, sample ids, test feedback, or sample-level rules. `record_key` is used only offline to align traces for diff.

## Compile-Scan Scope

| Benchmark | Run | Config | Output trace |
|---|---|---|---|
| LongMemEval-S probe50 | `v346_workspace_contract_budget_compile_scan_lme_probe50` | `configs/stage1_workspace_contract_budget_v346_compile_scan.json` | `outputs/diagnostic/v346_workspace_contract_budget_compile_scan_lme_probe50/traces.jsonl` |
| LoCoMo non-adversarial probe50 | `v346_workspace_contract_budget_compile_scan_locomo_probe50` | `configs/stage1_workspace_contract_budget_v346_compile_scan.json` | `outputs/diagnostic/v346_workspace_contract_budget_compile_scan_locomo_probe50/traces.jsonl` |

## Diff Summary

| Benchmark | Shared traces | Prompt changed | Evidence set changed | Evidence order changed | Avg context chars | Context-budget estimated chars | Dropped hits |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | 50 | 0 | 0 | 0 | `18034.42 -> 18034.42` | `17351.38 -> 17280.80` | `0.62 -> 0.54` |
| LoCoMo probe50 | 50 | 2 | 2 | 2 | `16342.96 -> 16343.74` | `6507.28 -> 6506.54` | `0.18 -> 0.18` |

Anchor retention did activate:

| Benchmark | Selected anchor source | Anchor samples | Retained anchors | Dropped anchors |
|---|---|---:|---:|---:|
| LongMemEval-S probe50 | `memory_workspace_contract` | 50 | 790 | 0 |
| LoCoMo probe50 | `memory_workspace_contract` | 50 | 923 | 0 |

## Diagnosis

v346 proves that `memory_workspace_contract_v1` can be used as a source-backed context-budget contract without breaking LongMemEval-S prompt construction, and without dropping any contract-selected anchors. However, it does not solve the query-token problem:

- LongMemEval-S prompt/context is unchanged.
- LoCoMo changes only 2/50 list-count prompts and slightly increases average context chars.
- The current `60/22k/32` budget is too loose; contract retention mostly protects anchors rather than reducing raw Memory Context.

No answer probe or judge was run, because the compile-scan shows no meaningful token reduction and small LoCoMo prompt drift. This is not an LTS candidate.

## Next Step

Keep the useful system direction, but do not use plain workspace-contract retention as the token-reduction mechanism. The next version should make build-owned workspace policy more selective: it should provide route/query-scoped source expansion, conflict verification, and component replacement contracts, then reduce query tokens by replacing redundant guide/workpad text rather than broadly trimming raw evidence.
