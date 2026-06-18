# Src Cleanup Audit 2026-06-18

## Scope

Audit `src/` after v142 formal evaluation to identify obsolete modules or compatibility code that can be safely removed without deleting useful ablation, verifier, guardrail, or experiment-replay assets.

## Actions

- Removed local untracked `src/**/__pycache__` directories. They were not tracked by git.
- Ran unit tests before cleanup: `python -m unittest discover -s src/tests` -> `224` tests passed.
- Checked references for `repair`, `rerank`, `turn_window_bm25`, `candidate_guide`, `context_pressure`, `operation_workpad`, `aggregation_report`, `update_conflict_guide`, and memory-state guide code.

## Findings

No whole tracked `src` module is currently safe to delete.

| Module/area | Decision | Reason |
|---|---|---|
| `src/memory/repair.py` | keep | still covered by tests and remains a verifier/guardrail asset, even if disabled in current LTS |
| `src/memory/rerank.py` | keep | pipeline and retrieval tests still cover rerank formatting/filtering; useful for #2 context noise/rerank risk |
| `TurnWindowBM25Retriever` and selected-context helpers | keep | pipeline/tests use them; relevant to #3 local evidence/context organization |
| `candidate_guide`, `operation_workpad`, `aggregation_report` compiler blocks | keep | tested and tied to retained diagnostic configs; deleting would remove ablation ability |
| `update_conflict_guide` compiler block | keep | directly related to #5; already configured in current lineage even though LoCoMo v142 applied count was `0` |
| `memory_state_guide` compiler block | keep | v141/v142 formal diagnostic asset; not LTS, but useful for next #5 design |

## Cleanup Direction

The main maintainability issue is not an obviously dead file; it is concentration of optional experiment logic in `compiler.py` and `pipeline.py`.

Recommended next cleanup should be structural and test-backed:

- split compiler optional guide builders into a smaller `compiler_guides.py` or equivalent local module;
- split pipeline config parsing/tracing helpers away from prediction orchestration;
- only delete a feature after all configs/docs/tests that justify it are explicitly retired.

Do not delete code only because a recent LTS has the corresponding option disabled. The project still needs controlled ablations for the five goal risks.
