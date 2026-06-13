# Diagnosis for stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a

## Summary

v33 top-60 retrieval expansion is a clean positive LoCoMo result, but it is not sufficient to reach the 0.78 target.

- DeepSeek judge valid-only accuracy: `0.7719298245614035`
- Invalid-as-wrong accuracy: `1188/1540 = 0.7714285714285715`
- Previous best v29/v32: `1173/1540 = 0.7616883116883116`
- Net gain: `+15` correct
- Target gap: `14` more correct examples needed for `0.78`

The useful signal is not "more context always helps". It is route-dependent: fact/list/profile improve, while temporal_lookup regresses.

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 60.0
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
- avg_context_chars: 15325.005844155845
- avg_query_tokens: 5191.105844155844
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
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v33_top60.sqlite
- answer_cache_namespace: stage1_retrieval_top60_v33_qwen3_30b
- answer_cache_hits: 31
- answer_cache_misses: 1509
- answer_cache_writes: 1509
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

## Evidence Recall

Offline evidence-label analysis:

- overall evidence_recall: `0.91796875`, n=`1536`
- type 1: `0.925531914893617`, n=`282`
- type 2: `0.9190031152647975`, n=`321`
- type 3: `0.6956521739130435`, n=`92`
- type 4: `0.93935790725327`, n=`841`

Compared with top-40 v29/v32 overall recall `0.8912760416666666`, source coverage is better. Accuracy only rises by 15 examples, so remaining errors are now more about answer selection, temporal disambiguation, and context noise than pure retrieval miss.

## v29 Delta

Offline judge comparison against `stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390`:

- both_correct: `1112`
- both_wrong: `291`
- gained: `76`
- lost: `61`

Route split:

- current_state: gained `1`, lost `0`, net `+1`
- fact_lookup: gained `50`, lost `34`, net `+16`
- list_count: gained `12`, lost `7`, net `+5`
- profile_preference: gained `5`, lost `3`, net `+2`
- temporal_lookup: gained `8`, lost `17`, net `-9`

Answer delta:

- changed WRONG_to_CORRECT: `68`
- same WRONG_to_CORRECT: `8`
- changed CORRECT_to_WRONG: `50`
- same CORRECT_to_WRONG: `11`

Interpretation: top-60 mostly helps when the missing fact was outside the old top-40 context. The losses include both changed answers and same-answer judge flips, but the temporal route shows a clear negative direction. Extra temporal evidence can introduce competing dates or older state, so future expansion must be selective.

## Clean Check

- Prediction input did not expose gold/reference answer, judge output, benchmark label, sample id, qid, or row index to pipeline modules.
- `record_key` was copied only by the runner for offline joining and did not enter route/retrieval/compiler/answer/verifier logic.
- DeepSeek judge and evidence recall read labels only after prediction completion.
- Dirty state at prediction run start came from user-edited docs, not prediction code or this run config.
- v33 method uses question-derived information_need and general retrieval budgets; it does not use benchmark-specific or sample-level rules.

## Decision

Keep v33 as the new LoCoMo best formal result, but do not run it directly on LongMemEval-S full. The previous mixed gate indicated top-60 can exceed the 6K query budget on LME-like long samples. LME needs a separate gate or a more selective budget.

The next method should be v34 route-budgeted retrieval:

- keep top-60 for `fact_lookup`, `list_count`, `profile_preference`, and `current_state`;
- use a narrower temporal retrieval/compile budget for `temporal_lookup`, likely matching v29 top-40;
- keep the rule general by keying only on question-derived information_need, not dataset labels or sample ids;
- run a no-label LoCoMo gate first, then full only if avg query tokens and answer max limits remain compliant.

This follows the external-method lesson from SimpleMem/DeepResearch style completeness-first retrieval while correcting the observed badcase pattern that completeness has to be controlled for temporal questions.

## Output Paths

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/traces.jsonl`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/evidence_recall.json`
- v29_comparison: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/judge_comparison_vs_v29.json`
