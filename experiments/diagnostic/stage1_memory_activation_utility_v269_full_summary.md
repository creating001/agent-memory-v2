# v269 Memory Activation Utility Full Summary

## Purpose

Validate a build-system risk reduction on top of v268. v269 keeps the governed typed-memory activation gate, then adds question-independent activation utility fields to each build memory object: utility score, bucket, role, priority, and reasons. The intent is to move more memory selection semantics into build/management metadata instead of adding query-time benchmark rules.

## Configuration

- config: `configs/stage1_memory_activation_utility_v269_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `ba7fd68`
- parent LTS: v268 `configs/stage1_governed_memory_activation_v268_seeded_qwen36_no_think_build4k_cached.json`
- added build fields: `activation_utility_score`, `activation_utility_bucket`, `activation_role`, `activation_priority`
- clean setting: no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules are used during prediction.

The full run summaries record `dirty=True` because local output/experiment artifacts were present or generated during the run. The method code and config are anchored at commit `ba7fd68`.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | answer diff vs v268 | activation utility manifest |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6462.478` | `0/500` | roles emitted for `500/500`; buckets high `57903`, medium `6` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6094.017532467533` | `0/1540` | roles emitted for `1540/1540`; buckets high `232409` |

Accuracy is inherited from v268 because full answer, prompt, final evidence, retrieval, pre-context-budget hits, memory hits, memory source hits, and token costs are identical.

## Diff

v269 vs v268 full:

```text
LME answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, pre_context_budget_diff=0, memory_hits_diff=0, memory_source_hits_diff=0, token_diff=0, answer_cache=500/0
LoCoMo answer_diff=0, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, pre_context_budget_diff=0, memory_hits_diff=0, memory_source_hits_diff=0, token_diff=0, answer_cache=1540/0
```

No changed-answer judge is needed.

## Activation Utility Counts

```text
LME role counts: episodic_candidate=7468, lifecycle_context=5499, prospective_candidate=14736, semantic_candidate=12204, stateful_candidate=17870, general_candidate=132
LME bucket counts: high=57903, medium=6
LoCoMo role counts: episodic_candidate=79615, lifecycle_context=13622, prospective_candidate=21928, semantic_candidate=21861, stateful_candidate=95383
LoCoMo bucket counts: high=232409
```

## Validation

```text
python -m json.tool configs/stage1_memory_activation_utility_v269_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/build.py scripts/run_stage1.py src/tests/test_clean_skeleton.py src/tests/test_build_memory.py
python -m unittest src.tests.test_build_memory src.tests.test_clean_skeleton
python -m unittest discover -s src/tests
git diff --check
```

Observed unit-test result: `346` tests passed.

## Decision

Promote v269 to local LTS.

Rationale: v269 reduces risk 1 and risk 5 by making memory object utility, role, priority, and activation reasons explicit build-stage outputs. It does not improve accuracy yet, but it preserves v268 full performance exactly while making the memory system more general and easier to ablate.

## Outputs

```text
outputs/diagnostic/stage1_memory_activation_utility_v269_lme_full/predictions.jsonl
outputs/diagnostic/stage1_memory_activation_utility_v269_lme_full/traces.jsonl
outputs/diagnostic/stage1_memory_activation_utility_v269_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_memory_activation_utility_v269_locomo_full/traces.jsonl
experiments/diagnostic/stage1_memory_activation_utility_v269_lme_full/
experiments/diagnostic/stage1_memory_activation_utility_v269_locomo_full/
```

## Next Steps

1. Turn activation utility into a real retrieval/context ablation that replaces fixed overflow/top-k behavior without increasing query complexity.
2. Continue moving event/state/profile/relation schema, temporal validity, and conflict resolution into build memory outputs.
3. Clean unused query compatibility code only after each branch is proven unused by tests and LTS traces.
