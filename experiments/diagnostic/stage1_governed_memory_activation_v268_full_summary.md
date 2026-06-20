# v268 Governed Memory Activation Full Summary

## Purpose

Validate a system-risk reduction on top of v267. v268 turns the build-stage `memory_system_governance_v1` manifest into an explicit, ablatable typed-memory activation policy: only `source_activation_ready` memory objects can drive build-memory BM25 source projection, slot/chain/operation/graph utility, and compiler memory records. Final answer evidence still resolves to raw Memory rows.

## Configuration

- config: `configs/stage1_governed_memory_activation_v268_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `2a20517`
- parent LTS: v267 `configs/stage1_memory_governance_v267_seeded_qwen36_no_think_build4k_cached.json`
- gate: `retrieval.memory_governance_activation.enabled=true`, `mode=source_activation_ready`
- clean setting: no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules are used during prediction.

The full run summaries record `dirty=True` because local output/cache/experiment artifacts were present or generated during the run. The method code and config are anchored at commit `2a20517`.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | answer diff vs v267 | governance activation |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6462.478` | `0/500` | applied `500/500`, filtered records `0` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6094.017532467533` | `0/1540` | applied `1540/1540`, filtered records `0` |

Accuracy is inherited from v267 because full answer, prompt, final evidence, retrieval, pre-context-budget hits, memory hits, memory source hits, and token costs are identical.

## Diff

v268 vs v267 full:

```text
LME answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, pre_context_budget_diff=0, memory_hits_diff=0, memory_source_hits_diff=0, token_diff=0, answer_cache=500/0
LoCoMo answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, pre_context_budget_diff=0, memory_hits_diff=0, memory_source_hits_diff=0, token_diff=0, answer_cache=1540/0
```

No changed-answer judge is needed.

## Validation

```text
python -m py_compile src/memory/build.py src/memory/pipeline.py src/tests/test_clean_skeleton.py src/tests/test_build_memory.py
python -m unittest discover -s src/tests
python -m json.tool configs/stage1_governed_memory_activation_v268_seeded_qwen36_no_think_build4k_cached.json
git diff --check
```

Observed unit-test result: `346` tests passed.

## Decision

Promote v268 to local LTS.

Rationale: v268 reduces typed-memory activation risk without changing performance. The project no longer merely audits source-backed activation readiness; the query path consumes that governance manifest as a real activation gate while keeping raw source rows as the final evidence authority.

## Outputs

```text
outputs/diagnostic/stage1_governed_memory_activation_v268_lme_full/predictions.jsonl
outputs/diagnostic/stage1_governed_memory_activation_v268_lme_full/traces.jsonl
outputs/diagnostic/stage1_governed_memory_activation_v268_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_governed_memory_activation_v268_locomo_full/traces.jsonl
experiments/diagnostic/stage1_governed_memory_activation_v268_lme_full/
experiments/diagnostic/stage1_governed_memory_activation_v268_locomo_full/
```

## Next Steps

1. Improve build memory object schema and lifecycle management so the governance gate has meaningful filtered cases beyond the current all-ready full data.
2. Continue query simplification by collapsing old route/selected-context/state-guide compatibility layers into candidate activation, context compiler, source-grounded answer, and consistency verifier.
3. Add a general consistency verifier for numeric, temporal, speaker, entity, state-conflict, and unsupported-answer errors.
