# v191 weekend parser gated LTS

## Decision

Promote `configs/stage1_weekend_parser_gated_v191_seeded_qwen36_no_think_build4k_cached.json` to the local qwen3.6 no-thinking LTS.

v191 inherits v184 predictions and dual-judge accuracy, while reducing the reproducibility risk introduced by rejected v187/v188 prompt/parser changes. The rejected `this/coming/upcoming weekend` event-time parser and prompt-map `mention_time` exposure are now opt-in. Legacy v184 past-weekend normalization (`last weekend`, `N weekends ago`) remains enabled, so parent prompts stay stable.

## Clean Scope

- Prediction uses only question text, raw Memory Context, source-linked build memory, route output, and prediction-time config.
- No gold answer, judge output, benchmark label, sample id, row index shortcut, test feedback, or sample-level rule is used.
- v187/v188 configs explicitly enable the rejected parser/prompt-map exposure for historical reproducibility; v191 explicitly disables them.

## Verification

Method commit: `3fbd033ba6d07d1c7c06447cd9e73c834b20186f`

Local checks:

```text
python -m unittest src.tests.test_compiler src.tests.test_clean_skeleton
python -m unittest discover -s src/tests
python -m py_compile src/memory/compiler.py src/memory/pipeline.py src/tests/test_compiler.py src/tests/test_clean_skeleton.py
python -m json.tool configs/stage1_weekend_parser_gated_v191_seeded_qwen36_no_think_build4k_cached.json
python -m json.tool configs/stage1_weekend_event_time_candidate_map_v187_seeded_qwen36_no_think_build4k_cached.json
python -m json.tool configs/stage1_temporal_ambiguity_event_time_map_v188_seeded_qwen36_no_think_build4k_cached.json
git diff --check
```

All checks passed.

## Results

| Run | Result |
|---|---|
| Activation probe r2 | v191 vs v184 prompt diff `0/3`, answer diff `0/3`, answer cache `3/0/0` |
| LongMemEval-S full r2 | v191 vs v184 prompt diff `0/500`, answer diff `0/500`, answer cache `500/0/0` |
| LoCoMo non-adversarial full r2 | v191 vs v184 prompt diff `0/1540`, answer diff `0/1540`, answer cache `1540/0/0` |

Inherited full dual-judge accuracy:

| Benchmark | strict / lenient |
|---|---:|
| LongMemEval-S full | `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0.793506 / 0.818831` |

No new full judge was run because v191 is prompt-identical and answer-identical to v184 on both full sets.

## Outputs

```text
experiments/diagnostic/stage1_weekend_parser_gated_v191_activation_probe_r2/
experiments/diagnostic/stage1_weekend_parser_gated_v191_lme_s_full_r2/
experiments/diagnostic/stage1_weekend_parser_gated_v191_locomo_nonadv_full_r2/
outputs/diagnostic/stage1_weekend_parser_gated_v191_activation_probe_r2/
outputs/diagnostic/stage1_weekend_parser_gated_v191_lme_s_full_r2/
outputs/diagnostic/stage1_weekend_parser_gated_v191_locomo_nonadv_full_r2/
```

The r2 manifests are dirty only because earlier local v191 diagnostic directories existed when the r2 runs were launched.

## Residual Risk

- v191 does not improve accuracy over v184; it reduces reproducibility and rejected-feature contamination risk while preserving performance.
- v184/v191 `exact_today` prompt-map activation can still be semantically noisy. The next algorithmic step should continue narrowing #5 query-time activation with stronger source/slot/action coverage, without hiding useful source-backed memory organization.
