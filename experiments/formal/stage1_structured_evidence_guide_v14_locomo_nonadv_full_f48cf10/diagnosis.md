# Diagnosis for stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10

## Summary

v14 在 LoCoMo non-adversarial full 上达到 1133/1540 = 0.735714 DeepSeek judge accuracy，超过 v13 temporal aid 的 0.721429、v12 source expansion 的 0.698701 和 clean naive RAG 的 0.698506。token gate 通过：avg_build_tokens 58386.008，avg_query_tokens 3818.198。

核心改动是 structured evidence guide：在 external_naive raw Memory Context 之外，额外给 answer model 一个 compact index，展示 retrieved rows 的 row_date/role/matched_terms/relative_time_mentions，并把 activated build memory 的 source_ids 映射回 prompt 内 Memory 编号。这个机制借鉴 A-Mem 的 memory neighborhood、HippoRAG/Hindsight 的 link expansion 与 provenance、xMemory 的 hybrid memory view，但暂不引入 heavy graph/PPR/query planner。

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 40.0
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.21103896103897
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.381168831168832
- avg_context_chars: 11952.301298701299
- avg_query_tokens: 3818.198051948052
- dense_protect_top_n: 32
- lexical_enabled: False
- session_bm25_enabled: False
- embedding_cache_hits: 7422
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 8
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- structured_guide: True
- structured_guide_max_rows: 12
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384

## Judge Diagnosis

- accuracy: 1133/1540 = 0.735714
- invalid_judgments: 0
- judge_tokens: prompt 496315, completion 155818, total 652133
- evidence_recall: 1339/1536 = 0.871745
- structured_guide_prompts: 1540/1540
- temporal_aid_prompts: 391/1540
- vs_v13: v14-only 123, v13-only 101, net +22
- vs_v12: v14-only 147, v12-only 90, net +57
- vs_naive_external_top40: v14-only 168, naive-only 110, net +58

Category delta vs v13:

- category 1: +28 / -30, net -2
- category 2: +34 / -25, net +9
- category 3: +13 / -7, net +6
- category 4: +48 / -39, net +9

## Interpretation

structured guide 对 LoCoMo 的收益是真实的：在不改 raw retrieval、不增加 lexical fusion 的情况下，accuracy 相比 v13 净增 22 条。收益集中在需要跨多轮组织证据的 category 2/3/4，说明 source-linked typed memory 作为 prompt 内索引可以降低 answer model 漏看或混淆证据的概率。

主要风险是泛化不稳。同一 v14 配置在 LongMemEval-S full 上为 352/500 = 0.704，低于 v12/v13 的 0.714；LME 的 knowledge-update、multi-session、assistant 类有回退。这说明 guide 当前过宽，会增加 query context 和 secondary-memory 噪声。不能简单把 guide 加长，也不能写 benchmark route 规则。

## Next Steps

- LoCoMo 主线更新为 v14 structured evidence guide。
- LME 主线仍保持 v12/v13；v14 只作为 LoCoMo-positive ablation。
- 下一版应做 general 的 high-confidence source-linked guide：减少 guide rows 或只展示与 activated memory/source expansion 强相关的 compact source map，目标是在保留 LoCoMo category 2/3/4 收益的同时恢复 LME。
- 继续从外部代码库提炼通用机制，优先考虑 raw episode + typed memory + provenance/backlink + compact compiler，不引入 benchmark-specific route 或样本级规则。
