# v274 Validity-Aware Graph Utility Full Summary

## Purpose

Use the v273 build-stage validity manifest in graph utility source selection without adding benchmark-specific rules or broad query-time prompt logic.

v274 keeps final evidence raw-source grounded: typed memory can rank and activate source candidates, but answer evidence still resolves back to raw Memory rows.

## Configuration

- config: `configs/stage1_validity_aware_graph_utility_v274_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `244bc07`
- parent LTS: v273 `configs/stage1_memory_object_validity_manifest_v273_seeded_qwen36_no_think_build4k_cached.json`
- source policy: `retrieval.graph_utility.source_selection_policy=validity_aware`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

Full run manifests are dirty only because v274 probe/full experiment directories were being generated after the method commit. The method/config/code change is locally committed at `244bc07`.

## Method Change

The graph utility source selector now prefers source-backed, higher-confidence, temporally anchored memory records. For current/non-historical questions it favors open state or event-scoped records before closed records; for historical questions it favors closed and event-scoped records before open records. The change does not alter route selection, top-k, answer prompt, answer cache seed logic, or the rule that final evidence is raw source text.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | note |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6463.04` | changed-answer paired judge delta `0 / 0` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.8493506493505` | answer diff `0/1540`; inherited v273 accuracy |

Auxiliary lexical metrics, offline-only and not used as the main performance metric:

| Benchmark | exact | F1 | unigram BLEU |
|---|---:|---:|---:|
| LongMemEval-S full | `0.432000` | `0.6382564639794627` | `0.5945745847818985` |
| LoCoMo non-adversarial full | `0.2422077922077922` | `0.5375986999424064` | `0.4833665475326201` |

## Full Diff

v274 vs v273 full:

```text
LME: answer_diff=1/500, prompt_diff=2, route_diff=0, final_evidence_diff=2, retrieval_diff=25, token_diff=2, answer_cache=498/2, policy=validity_aware 500/500
LoCoMo: answer_diff=0/1540, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=33, token_diff=0, answer_cache=1540/0, policy=validity_aware 1540/1540
```

The single LME changed answer is `dd0bbac643885d79aa0ac2a2`; both v273 and v274 are judged wrong by both flash judges, so strict/lenient delta is `0 / 0`.

## Token Cost

| Benchmark | v273 avg query tokens | v274 avg query tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S full | `6462.478` | `6463.04` | `+0.562` |
| LoCoMo non-adversarial full | `6093.8493506493505` | `6093.8493506493505` | `0` |

Build tokens are unchanged: LME `85393.566`, LoCoMo `62015.57402597403`.

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking:

| Benchmark | changed answers | base strict/lenient | new strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `1` | `0/1` strict, `0/1` lenient | `0/1` strict, `0/1` lenient | `0 / 0` |
| LoCoMo non-adversarial full | `0` | inherited | inherited | `0 / 0` |

Judge output paths:

```text
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full_changed_vs_v273/lme_v273_dual_judge.json
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full_changed_vs_v273/lme_v274_dual_judge.json
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full_changed_vs_v273/lme_v273_deepseek_judge_flash_1.json
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full_changed_vs_v273/lme_v273_deepseek_judge_flash_2.json
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full_changed_vs_v273/lme_v274_deepseek_judge_flash_1.json
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full_changed_vs_v273/lme_v274_deepseek_judge_flash_2.json
```

## Validation

```text
python -m json.tool configs/stage1_validity_aware_graph_utility_v274_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/pipeline.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_clean_skeleton
python -m unittest discover -s src/tests
git diff --check
```

Observed unit-test result before the method commit: `355` tests passed.

## Decision

Promote v274 to local LTS.

Rationale: v274 reduces build-system risk by making validity/source-confidence/temporal-scope fields influence graph utility source selection, instead of only recording them in the manifest. It keeps the change clean and narrow, does not add benchmark-specific route or answer rules, keeps final evidence raw-source grounded, and has no DeepSeek dual judge accuracy regression on LongMemEval-S or LoCoMo full.

## Outputs

```text
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_probe50/predictions.jsonl
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_probe50/traces.jsonl
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_locomo_probe50/predictions.jsonl
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_locomo_probe50/traces.jsonl
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full/predictions.jsonl
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full/traces.jsonl
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_validity_aware_graph_utility_v274_locomo_full/traces.jsonl
experiments/diagnostic/stage1_validity_aware_graph_utility_v274_lme_probe50/
experiments/diagnostic/stage1_validity_aware_graph_utility_v274_locomo_probe50/
experiments/diagnostic/stage1_validity_aware_graph_utility_v274_lme_full/
experiments/diagnostic/stage1_validity_aware_graph_utility_v274_locomo_full/
```

## Next Steps

1. Move more query-time compatibility logic into build/management: lifecycle consolidation, conflict clustering, same-slot source coverage, and utility source policy.
2. Keep changed-answer paired judge as the default promotion gate when behavior changes only a small subset.
3. Continue small `src/` cleanup after trace diffs prove a branch is unused or redundant.
