# v283 Order-Safe Value Parser Full Summary

## Purpose

Reduce benchmark-shaped query logic in `Update/Conflict Candidate Chain`. v280 used a fixed quantity-unit whitelist such as stars, followers, pages, and miles. v283 replaces that with a general source-text value parser while protecting event-order/timeline questions from non-event unit expansion.

## Method Change

- v281 introduced generic value extraction: protected time/currency/frequency forms plus number-and-domain-unit spans trimmed by generic context stopwords.
- v282 showed that simply disabling conflict-chain activation for event-order questions can regress ordering.
- v283 keeps domain-unit extraction for scalar/count/current-value conflicts, but uses scalar-only extraction for event-order, sequence, and timeline questions.
- Final evidence remains raw Memory rows; the value parser only organizes prompt-side conflict candidates.

## Configuration

- config: `configs/stage1_order_safe_value_parser_v283_seeded_qwen36_no_think_build4k_cached.json`
- method/config commit: `65cd073`
- parent LTS: v280 `configs/stage1_manifest_state_guide_v280_seeded_qwen36_no_think_build4k_cached.json`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Main Accuracy

v283 changes LongMemEval answers on 3/500 examples and leaves LoCoMo unchanged. Changed-answer dual DeepSeek flash judge improves LongMemEval by `+1/+1` strict/lenient relative to v280, so full accuracy is:

| Benchmark | strict / lenient | avg build tokens | avg query tokens |
|---|---:|---:|---:|
| LongMemEval-S full | `0.834000 / 0.846000` | `85393.566` | `6464.954` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.794155844156` |

## Full Diff Vs v280

```text
LME: answer_diff=3/500, prompt_diff=23, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=22, build_memory_diff=0, answer_cache=500/0
LoCoMo: answer_diff=0/1540, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=0, answer_cache=1540/0
```

## Changed-Answer Judge

Changed LME examples vs v280:

```text
v280 changed subset: strict/lenient 2/3, 2/3
v283 changed subset: strict/lenient 3/3, 3/3
delta: +1 strict, +1 lenient
```

The improvement is the YouTube/TikTok views total (`1,998`). The two other changed answers are equivalent wording (`12,000 people`; shortened engineer-lead phrasing). The v281/v282 trip-order regression is removed in v283 by scalar-only event-order extraction.

## Validation

```text
python -m py_compile src/memory/compiler.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_update_conflict_guide_keeps_domain_specific_units src.tests.test_clean_skeleton.CleanSkeletonTest.test_update_conflict_guide_uses_scalar_values_for_event_order_questions src.tests.test_clean_skeleton.CleanSkeletonTest.test_update_conflict_guide_is_narrow_and_source_preserving src.tests.test_clean_skeleton.CleanSkeletonTest.test_update_conflict_guide_adds_aggregation_operand_rule
python -m unittest discover -s src/tests
git diff --check
```

Observed result: `358` tests passed.

## Decision

Promote v283 to local LTS.

Rationale: v283 reduces a concrete design-for-benchmark risk in query-side conflict organization, preserves event-order behavior, improves LongMemEval judge accuracy by one strict/lenient answer, and leaves LoCoMo unchanged. It is still not the final architecture target: `operation_manifest_v1` should next be consumed more directly by context organization and verifier logic.

## Outputs

```text
outputs/diagnostic/stage1_order_safe_value_parser_v283_lme_full/predictions.jsonl
outputs/diagnostic/stage1_order_safe_value_parser_v283_lme_full/traces.jsonl
outputs/diagnostic/stage1_order_safe_value_parser_v283_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_order_safe_value_parser_v283_locomo_full/traces.jsonl
outputs/diagnostic/stage1_order_safe_value_parser_v283_lme_changed_vs_v280/
experiments/diagnostic/stage1_order_safe_value_parser_v283_lme_full/
experiments/diagnostic/stage1_order_safe_value_parser_v283_locomo_full/
```

## Next Steps

1. Move more query-side conflict/operation logic behind build-owned `operation_manifest_v1` instead of adding new prompt-only guides.
2. Add a build-owned scalar value/conflict object view so source-backed quantities can participate in state management and verification without benchmark unit lists.
3. Continue small `src/` cleanup after each version, especially old compatibility paths around state/update guides.
