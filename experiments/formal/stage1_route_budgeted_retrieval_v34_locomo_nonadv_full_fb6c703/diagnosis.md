# Diagnosis for stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703

## Summary

v34 route-budgeted retrieval is the current best LoCoMo result.

- DeepSeek judge valid-only accuracy: `0.7797270955165692`
- Invalid-as-wrong accuracy: `1200/1540 = 0.7792207792207793`
- Previous best v33: `1188/1540 = 0.7714285714285715`
- v29/v32: `1173/1540 = 0.7616883116883116`
- Net vs v33: `+12` correct
- Net vs v29: `+27` correct
- Target gap: `2` more correct examples needed for `0.78` under invalid-as-wrong accounting.

The main hypothesis is confirmed: top-60 helps non-temporal source coverage, but temporal questions need narrower context to avoid old-date and competing-event noise.

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 55.61038961038961
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.11233766233767
- build_memory_temporal_fields: False
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.37922077922078
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 14478.938311688311
- avg_query_tokens: 4920.3266233766235
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 55.61038961038961
- avg_effective_dense_top_k: 55.61038961038961
- avg_effective_dense_protect_top_n: 44.48831168831169
- dense_protect_top_n: 48
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 7422
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_event_contract: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- structured_guide: True
- structured_guide_max_rows: 12
- structured_guide_include_rows: True
- structured_guide_include_memory: False
- structured_guide_disabled_signals: ['personalized_recommendation']
- structured_answer_contract: False
- structured_answer_contract_information_needs: None
- structured_answer_contract_max_items: 10
- evidence_report_contract: True
- evidence_report_information_needs: ['current_state', 'fact_lookup', 'list_count', 'profile_preference', 'temporal_lookup']
- evidence_report_max_items: 8
- evidence_report_detail: False
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000}}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v34_route_budgeted.sqlite
- answer_cache_namespace: stage1_route_budgeted_retrieval_v34_qwen3_30b
- answer_cache_hits: 1207
- answer_cache_misses: 333
- answer_cache_writes: 333
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: False
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_information_needs: None
- answer_repair_triggered_count: 0
- answer_repair_triggered_rate: 0.0
- answer_repair_applied_count: 0
- answer_repair_applied_rate: 0.0
- answer_repair_total_query_tokens: 0
- answer_repair_avg_query_tokens_when_triggered: None
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Route Budget Check

- `temporal_lookup`: 338 examples, top_k `40`, dense_top_k `40`, dense_protect_top_n `32`, compiled evidence rows `40`.
- `fact_lookup`: 1018 examples, top_k `60`, dense_top_k `60`, dense_protect_top_n `48`, compiled evidence rows `60`.
- `list_count`: 131 examples, top_k `60`, dense_top_k `60`, dense_protect_top_n `48`, compiled evidence rows `60`.
- `profile_preference`: 49 examples, top_k `60`, dense_top_k `60`, dense_protect_top_n `48`, compiled evidence rows `60`.
- `current_state`: 4 examples, top_k `60`, dense_top_k `60`, dense_protect_top_n `48`, compiled evidence rows `60`.

## Evidence Recall

Offline evidence-label analysis:

- overall evidence_recall: `0.9153645833333334`, n=`1536`
- type 1: `0.925531914893617`, n=`282`
- type 2: `0.9065420560747663`, n=`321`
- type 3: `0.6956521739130435`, n=`92`
- type 4: `0.93935790725327`, n=`841`

v34 recall is slightly lower than v33 top-60 (`0.91796875`) because temporal rows use top-40, but accuracy improves. This indicates context precision matters more than maximum recall for temporal_lookup.

## v33 Delta

Offline judge comparison against `stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a`:

- both_correct: `1156`
- both_wrong: `308`
- gained: `44`
- lost: `32`
- net: `+12`

Route split:

- current_state: all `4` both_correct
- fact_lookup: gained `23`, lost `18`, net `+5`
- list_count: gained `1`, lost `1`, net `0`
- profile_preference: gained `1`, lost `1`, net `0`
- temporal_lookup: gained `19`, lost `12`, net `+7`

Answer delta:

- changed WRONG_to_CORRECT: `17`
- same WRONG_to_CORRECT: `27`
- changed CORRECT_to_WRONG: `10`
- same CORRECT_to_WRONG: `22`

The temporal net gain confirms the route-budgeted design. The same-answer judge flips show that a small number of gains/losses are evaluator sensitivity rather than true answer changes; future diagnosis should separate actual answer changes from judge variance.

## v29 Delta

Offline judge comparison against `stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390`:

- both_correct: `1118`
- both_wrong: `285`
- gained: `82`
- lost: `55`
- net: `+27`

Route split:

- current_state: net `+1`
- fact_lookup: net `+21`
- list_count: net `+5`
- profile_preference: net `+2`
- temporal_lookup: net `-2`

This is acceptable because v34 primarily recovers v33's non-temporal source coverage gains while limiting temporal regression. It still does not solve temporal completely.

## Clean Check

- Prediction input did not expose gold/reference answer, judge output, benchmark label, sample id, qid, or row index to pipeline modules.
- `record_key` was copied only by the runner for offline joining and did not enter route/retrieval/compiler/answer/verifier logic.
- DeepSeek judge, evidence recall, and comparison scripts read labels/judge only after prediction completion.
- Dirty state at prediction run start came from user-edited docs, not prediction code or v34 config.
- v34 route budgeting keys only on question-derived generic `information_need`, not benchmark labels or sample-level rules.

## Decision

Keep v34 as the new LoCoMo best formal result. It is close enough to the 0.78 target that the next move should be a targeted, general fix rather than a full new build method.

Recommended next steps:

- inspect the 32 v34-v33 lost cases and the 44 gained cases, separating answer changes from same-answer judge flips;
- prioritize general answer extraction/format stability, because some losses are identical answers judged differently or JSON leakage into final answer;
- inspect remaining temporal lost cases before changing temporal budget again;
- do a separate LongMemEval-S token gate before any LME full run.

## Output Paths

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/traces.jsonl`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/evidence_recall.json`
- v33_comparison: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/judge_comparison_vs_v33.json`
- v29_comparison: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/judge_comparison_vs_v29.json`
