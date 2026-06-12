# Diagnosis for formal/stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached

## Summary

本次 v3 是一个 clean 的 query-side compiler 消融：复用 v1 冷构建得到的 build cache，只改变检索清洗、memory 排序和 typed-section context 组织。DeepSeek judge accuracy 为 0.558（279/500），相对 v2 的 0.540 净增 9 个样本，相对 v1 的 0.528 净增 15 个样本。

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 12.49
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 7.756
- avg_memory_source_hits: 7.528
- avg_context_chars: 20335.074
- avg_query_tokens: 5274.212
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
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.
- deepseek_judge_accuracy: 0.558
- deepseek_judge_correct: 279
- deepseek_judge_wrong: 221
- deepseek_judge_usage_total_tokens: 116961
- offline_evidence_recall: 0.976
- offline_evidence_recall_n: 500

## DeepSeek Judge By Type

| type | correct | total | accuracy |
|---|---:|---:|---:|
| knowledge-update | 57 | 78 | 0.7308 |
| multi-session | 51 | 133 | 0.3835 |
| single-session-assistant | 50 | 56 | 0.8929 |
| single-session-preference | 8 | 30 | 0.2667 |
| single-session-user | 62 | 70 | 0.8857 |
| temporal-reasoning | 51 | 133 | 0.3835 |

## Offline Evidence Recall

| type | n | evidence_recall |
|---|---:|---:|
| knowledge-update | 78 | 1.0000 |
| multi-session | 133 | 0.9624 |
| single-session-assistant | 56 | 1.0000 |
| single-session-preference | 30 | 0.9333 |
| single-session-user | 70 | 0.9857 |
| temporal-reasoning | 133 | 0.9699 |

## Diagnosis

- typed memory sections 和 question-overlap memory ordering 是有效的 clean 正向消融，主要提升 knowledge-update，也对部分 multi-session 样本有帮助。
- 该收益仍然偏浅，说明问题不只是 answer prompt 组织；multi-session 和 temporal-reasoning 仍低于 40%，需要更强的 build-stage memory management 和 temporal/profile/event 结构。
- offline evidence recall 已达 0.976，multi-session 和 temporal-reasoning 也分别为 0.9624 和 0.9699；因此下一步不能只扩大 top-k 或无差别增加 context token，重点应放在证据组织、状态链、时间规范化和多证据聚合。
- single-session-user / assistant 已经较强，下一步不应为了这些类型牺牲总体检索精度；应重点解决跨会话聚合、时间顺序、状态更新和偏好稳定性。
- single-session-preference 仍很弱，当前 typed records 对稳定偏好、一次性事件和 profile state 的区分不够，容易漏掉可用于个性化回答的信息。
- avg query tokens 5274.212，仍在 6K 主线预算内；avg build tokens 为 0 是因为本次完全复用 build cache，并不代表真实冷构建成本为 0。
- 本次 judge 在预测完成后离线运行；judge 输出、gold、question_type、record_key 只进入实验记录和诊断，不能进入 prediction pipeline。

## Next Steps

- 保留 v3 作为当前 LME query-side best，不再围绕小 prompt 细节盲目试错。
- 下一轮优先设计 general 的 build-stage memory manager：profile/event 分离、temporal validity、conflict/supersede chain、source-backed aggregation。
- 新方法必须有显式配置开关，冷构建前先做 aggregate badcase 诊断，确认改动目标是 multi-session、temporal 和 preference 的通用错误机制。
