# v278 State/Profile Tier Activation Full Summary

## Purpose

Use the build memory tier manifest as a real activation signal while keeping query-time behavior narrow and general.

v278 inherits v276's memory tier/source-policy system and v277's tier-aware activation priority ordering, but scopes the behavior to `current_state` and `profile_preference` only. It does not apply tier activation to list-count or temporal questions after v277 showed high prompt churn there.

## Method Lens

- ReMe / LightMem: working-memory style state should influence active recall, not just be logged.
- LangMem / Mem0: durable memory systems need explicit update/lifecycle state and retrieval-time activation policy.
- Graphiti: temporal/provenance state should remain source-backed and non-destructive.

Takeaway for v278: build memory can expose tier/utility state for retrieval activation, but broad use should be gated by general information need and validated with changed-answer judge before promotion.

## Configuration

- config: `configs/stage1_state_profile_tier_activation_v278_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `00ebea1`
- config commit: `c64a13e`
- parent LTS: v276 `configs/stage1_memory_tier_manifest_v276_seeded_qwen36_no_think_build4k_cached.json`
- activation scope: `current_state`, `profile_preference`
- activation parameters: `pool_k=32`, `score_boost=0.25`, `max_rank=64`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Method Change

`src/memory/build.py` adds `tier_order` to `memory_activation_utility_v1` and uses `memory_tier` in the build-side activation-priority sort key. The v278 config enables `retrieval.memory_activation_priority` only for state/profile information needs, so typed memory tier/utility can softly reorder source-backed memory hits before they are projected back to raw source rows.

No answer prompt rule, verifier rewrite, benchmark type, sample id, label, or judge signal is used. Final answer evidence remains raw Memory rows.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | note |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6463.628` | changed-answer judge delta `0 / 0` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.794155844156` | changed-answer judge delta `0 / 0` |

Auxiliary lexical metrics, offline-only and not used as the main performance metric:

| Benchmark | exact | F1 | unigram BLEU |
|---|---:|---:|---:|
| LongMemEval-S full | `0.434000` | `0.6390256947486934` | `0.5956856958930096` |
| LoCoMo non-adversarial full | `0.2422077922077922` | `0.5375795889021392` | `0.48335486295031593` |

## Full Diff

v278 vs v276 full:

```text
LME: answer_diff=2/500, prompt_diff=2, route_diff=0, final_evidence_diff=5, retrieval_diff=12, token_diff=2, build_memory_diff=500, answer_cache=498/2, priority_applied=34, priority_reordered=6
LoCoMo: answer_diff=4/1540, prompt_diff=13, route_diff=0, final_evidence_diff=24, retrieval_diff=25, token_diff=13, build_memory_diff=1540, answer_cache=1528/12, priority_applied=49, priority_reordered=38
```

The build memory diff is expected: v278 changes activation-priority policy metadata while keeping the v276 tier/source-policy graph.

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking:

| Benchmark | changed answers | base strict/lenient | v278 strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full changed vs v276 | `2` | `2 / 2` | `2 / 2` | `0 / 0` |
| LoCoMo full changed vs v276 | `4` | `4 / 4` | `4 / 4` | `0 / 0` |

## Token Cost

| Benchmark | v276 avg query tokens | v278 avg query tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S full | `6463.04` | `6463.628` | `+0.588` |
| LoCoMo non-adversarial full | `6093.8493506493505` | `6093.794155844156` | `-0.0551948051945` |

Build tokens are unchanged: LME `85393.566`, LoCoMo `62015.57402597403`.

## Tier And Activation Coverage

| Benchmark | tier manifest | working | long-term | archival | quarantine | priority applied / reordered |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` | `32606` | `19804` | `5499` | `0` | `34 / 6` |
| LoCoMo non-adversarial full | `1540/1540` | `117311` | `101476` | `13622` | `0` | `49 / 38` |

## Validation

```text
python -m json.tool configs/stage1_state_profile_tier_activation_v278_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/build.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_system_graph_records_schema_and_quality src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_activation_priority_reorders_with_manifest_prior src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_activation_priority_is_route_scoped
python -m unittest discover -s src/tests
python scripts/evaluate_predictions.py --predictions outputs/diagnostic/stage1_state_profile_tier_activation_v278_lme_full/predictions.jsonl --labels outputs/prepare_longmemeval_s_cleaned/labels.jsonl --output outputs/diagnostic/stage1_state_profile_tier_activation_v278_lme_full/offline_metrics.json
python scripts/evaluate_predictions.py --predictions outputs/diagnostic/stage1_state_profile_tier_activation_v278_locomo_full/predictions.jsonl --labels outputs/prepare_locomo_non_adversarial/labels.jsonl --output outputs/diagnostic/stage1_state_profile_tier_activation_v278_locomo_full/offline_metrics.json
git diff --check
```

Observed unit-test result before the method commit: `355` tests passed.

## Decision

Promote v278 to local LTS.

Rationale: v278 makes build-time tier/utility state participate in retrieval activation, reduces the risk that memory tiers are only decorative traces, and avoids the broader list/temporal churn observed in v277. The full changed-answer judge shows no strict or lenient accuracy regression; token cost is effectively unchanged and remains below the 8K hard diagnostic line.

## Outputs

```text
outputs/diagnostic/stage1_state_profile_tier_activation_v278_lme_probe50/predictions.jsonl
outputs/diagnostic/stage1_state_profile_tier_activation_v278_lme_probe50/traces.jsonl
outputs/diagnostic/stage1_state_profile_tier_activation_v278_locomo_probe50/predictions.jsonl
outputs/diagnostic/stage1_state_profile_tier_activation_v278_locomo_probe50/traces.jsonl
outputs/diagnostic/stage1_state_profile_tier_activation_v278_lme_full/predictions.jsonl
outputs/diagnostic/stage1_state_profile_tier_activation_v278_lme_full/traces.jsonl
outputs/diagnostic/stage1_state_profile_tier_activation_v278_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_state_profile_tier_activation_v278_locomo_full/traces.jsonl
outputs/diagnostic/stage1_state_profile_tier_activation_v278_lme_full_changed_vs_v276/
outputs/diagnostic/stage1_state_profile_tier_activation_v278_locomo_full_changed_vs_v276/
experiments/diagnostic/stage1_state_profile_tier_activation_v278_lme_probe50/
experiments/diagnostic/stage1_state_profile_tier_activation_v278_locomo_probe50/
experiments/diagnostic/stage1_state_profile_tier_activation_v278_lme_full/
experiments/diagnostic/stage1_state_profile_tier_activation_v278_locomo_full/
```

## Next Steps

1. Add build-owned consolidation/conflict clusters and make them consumable through the same activation policy.
2. Probe whether `memory_state_guide` current-state branches can be deleted or reduced after tier activation, using answer-equivalent diffs.
3. Keep list-count and temporal tier activation disabled until a more selective source-utility gate reduces churn.
