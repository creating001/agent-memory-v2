# Diagnosis for formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached

## Summary

v5 在 v4 基础上给 temporal workpad 增加 raw row text 中相对时间表达的归一化候选，例如 `yesterday -> 2023-05-07`。这个改动是 clean 的 query-side ablation：预测阶段只使用原始对话文本和可见时间戳，不读取 gold、judge、question_type、record_key 或样本反馈。

离线 DeepSeek judge 结果为 295/500 = 0.5900，低于 v4 的 0.5960。该方法暂不应作为主线默认配置。

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 12.522
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 7.756
- avg_memory_source_hits: 7.528
- avg_context_chars: 21313.04
- avg_query_tokens: 5683.876
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 193
- session_bm25_applied_rate: 0.386
- embedding_cache_enabled: True
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- evidence_order: question_overlap
- memory_order: question_overlap
- memory_layout: typed_sections
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 16
- route_guidance: True
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- enable_recommendation_profile_patterns: True
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Offline Judge

- accuracy: 295/500 = 0.5900
- v4 baseline: 298/500 = 0.5960
- net change vs v4: -3 correct
- changed records: 12 improved, 15 regressed
- judge usage: prompt_tokens=77934, completion_tokens=36249, total_tokens=114183

## By Type

- knowledge-update: 56/78 = 0.7179, net -1 vs v4
- multi-session: 47/133 = 0.3534, net 0 vs v4
- single-session-assistant: 48/56 = 0.8571, net 0 vs v4
- single-session-preference: 8/30 = 0.2667, net -3 vs v4
- single-session-user: 62/70 = 0.8857, net +1 vs v4
- temporal-reasoning: 74/133 = 0.5564, net 0 vs v4

## Evidence Recall

- overall evidence recall: 0.978 over 500 samples
- temporal-reasoning recall: 0.9699
- multi-session recall: 0.9624
- single-session-preference recall: 0.9667

高 evidence recall 但 accuracy 没提升，说明 LME 当前主要瓶颈不是证据是否被取到，而是 build memory / compiler / answer 对证据的状态管理和取舍仍不够稳定。

## Interpretation

- v5 的相对时间文本提示没有带来 temporal-reasoning 净收益：5 个 temporal 样本改善、5 个 temporal 样本退化。
- single-session-preference 净退化 3 个样本，说明向 prompt 加更多时间候选可能干扰偏好类问题的稳定抽取，即使这不是 benchmark-specific 规则。
- avg_query_tokens 从 v4 的 5760.424 降到 5683.876，仍接近 6K 预算；单纯加 answer-time hint 不是可靠方向。

## Next Steps

- 保留 v5 作为 negative ablation，不推进 LoCoMo full，除非后续有更强理由证明 LoCoMo 特定 temporal 问题值得单独验证。
- 下一步优先做 build-stage memory 管理：显式区分 event / profile / state，维护 temporal validity、supersedes 和 raw source back-links。
- 新方法需要继续保持 general，不能按 LongMemEval/LoCoMo 类型、样本 id、gold 或 judge 反馈写规则。
