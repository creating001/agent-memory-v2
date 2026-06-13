# Diagnosis for stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9

## Summary

v35 answer format guard reaches the LoCoMo 0.78 baseline target under valid-only DeepSeek judge accuracy.

- DeepSeek judge valid-only accuracy: `0.7803768680961664`
- Invalid-as-wrong accuracy: `1201/1540 = 0.7798701298701298`
- Previous best v34: `1200/1540 = 0.7792207792207793`
- v33: `1188/1540 = 0.7714285714285715`
- v29/v32: `1173/1540 = 0.7616883116883116`

This is a close-margin positive result. Only 6 predictions changed from v34, and same-answer judge flips remain visible, so reporting must include both valid-only and invalid-as-wrong numbers.

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
- avg_query_tokens: 4920.572727272727
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
- answer_cache_path: outputs/cache/qwen3_answer_v35_format_guard.sqlite
- answer_cache_namespace: stage1_answer_format_guard_v35_qwen3_30b
- answer_cache_hits: 1540
- answer_cache_misses: 0
- answer_cache_writes: 0
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 2
- answer_finalizer_applied_rate: 0.0012987012987012987
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

## Prediction Delta

Compared with v34 predictions:

- changed predictions: `6/1540`
- JSON-like final answers: `4 -> 1`
- decimal duration answers: `2 -> 0`
- finalizer applied: `2`, both reason `duration_decimal_rounding`
- answer cache hits/misses/writes: `1540/0/0`

Changed answers:

- JSON salvage produced concise final answers for malformed or nested `json_answer` responses.
- Duration rounding changed `2.29 weeks -> 2 weeks` and `3.43 weeks -> 3 weeks`.
- One cached raw_response reparse changed an insufficient-information answer to a longer still-insufficient answer; this is a side effect of re-parsing cached raw response rather than reusing the older cached answer field.

## Evidence Recall

Offline evidence-label analysis:

- overall evidence_recall: `0.9153645833333334`, n=`1536`
- type 1: `0.925531914893617`, n=`282`
- type 2: `0.9065420560747663`, n=`321`
- type 3: `0.6956521739130435`, n=`92`
- type 4: `0.93935790725327`, n=`841`

Retrieval is unchanged from v34, so evidence recall is unchanged.

## v34 Delta

Offline judge comparison against `stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703`:

- both_correct: `1174`
- both_wrong: `313`
- gained: `27`
- lost: `26`
- net: `+1`
- n_answer_changed: `6`

Answer delta:

- changed WRONG_to_CORRECT: `3`
- changed both_correct: `2`
- changed both_wrong: `1`
- same WRONG_to_CORRECT: `24`
- same CORRECT_to_WRONG: `26`

Interpretation: the method change itself plausibly fixes a few answer-format cases, but most v34-v35 judge movement comes from same-answer judge variance. The run is still valid as a full DeepSeek judge result, but it should not be overclaimed as a large method gain.

## v33/v29 Delta

Against v33:

- gained: `42`
- lost: `29`
- net: `+13`
- temporal_lookup net `+13`

Against v29:

- gained: `81`
- lost: `53`
- net: `+28`

v35 therefore preserves the main v34 route-budgeted retrieval gain and adds a small answer-format improvement.

## Clean Check

- Prediction input did not expose gold/reference answer, judge output, benchmark label, sample id, qid, row index, category, or question_type to prediction modules.
- Parser salvage and duration rounding use only prediction-time artifacts: raw response, cached raw response, draft answer, and question text.
- DeepSeek judge, evidence recall, and comparison scripts read labels/judge only after prediction completion.
- Dirty state at prediction run start came from user-edited docs, not prediction code or v35 config.
- No sample-level rule was added; duration rounding is keyed on generic `how many <time unit>` question text and a single decimal duration answer.

## Decision

Keep v35 as the current LoCoMo best formal result. It reaches the valid-only 0.78 target, while invalid-as-wrong remains just below target because of one invalid judge output.

Recommended next steps:

- run a LongMemEval-S token gate with v35 before any LME full run;
- inspect the one invalid DeepSeek judgment and consider adding a general judge retry policy for invalid judge responses in the evaluation script;
- continue method work on build/query memory quality rather than more LoCoMo-only answer formatting.

## Output Paths

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/traces.jsonl`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/evidence_recall.json`
- v34_comparison: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/judge_comparison_vs_v34.json`
- v33_comparison: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/judge_comparison_vs_v33.json`
- v29_comparison: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/judge_comparison_vs_v29.json`
