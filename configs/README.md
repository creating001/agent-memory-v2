# 配置入口

当前只保留主线需要的配置：

- `stage1_clean_skeleton.json`：无 LLM smoke / 单元测试级骨架配置。
- `stage1_strict_cached.json`：Stage-1 strict baseline，带 embedding cache。
- `stage1_route_guidance_cached.json`：ablation 配置，在 strict baseline 上增加通用 route guidance。
- `stage1_build_memory_cached.json`：早期 build-stage LLM typed memory 配置，包含 memory cache、typed-memory retrieval 和 route guidance。
- `stage1_query_retrieval_v2_cached.json`：query-side ablation，复用 `stage1_build_memory_cached` 的 cold build cache，只改通用 stopword filtering、evidence ordering 和 temporal hints。
- `stage1_memory_compiler_v3_cached.json`：query-side memory compiler ablation，在 v2 上增加 typed memory sections 和 question-overlap memory ordering，继续复用 cold build cache。
- `stage1_temporal_preference_v4_cached.json`：query-side ablation，在 v3 上增加通用 temporal calculation workpad 和 personalized recommendation route，借鉴 SimpleMem 的 intent-aware retrieval、Zep/Graphiti 的 temporal validity 思路，以及 Memobase/Hindsight 的 profile/preference 分离；仍只使用问题文本、问题时间、raw evidence 和 build memory，不使用任何标签或样本级规则。
- `stage1_temporal_preference_v4_1_cached.json`：query-side ablation，在 v4 上把 temporal workpad 收紧到确实需要 duration / ago / between / order 计算的 temporal/current 问题，并限制 workpad 行数和 pairwise gap 数，目标是降低 token 成本和 multi-session 噪声。
- `stage1_temporal_text_v5_cached.json`：query-side ablation，在 v4 上打开 clean temporal text normalization，把 raw row text 中的 yesterday / last Sunday / two weeks ago 等通用相对时间表达写入 workpad 候选；借鉴 SimpleMem 的时间归一化和 Graphiti/Zep 的 temporal validity，但不读 gold、category、judge 或样本 id。
- `stage1_route_priority_v6_cached.json`：query-side ablation，在 v4 上显式打开 `temporal_priority_over_recent`，让明确的 when / duration / days 等 temporal intent 优先于 latest / current 等描述性 recent 词；借鉴 Hindsight/GAM 的 question-intent-first compiler 思路，不使用 gold、category、judge 或样本 id。
- `stage1_memory_validity_v7_cached.json`：build-memory management ablation，在 v4 上给 typed memory 暴露 valid_from / valid_to，并仅对 temporal_lookup / list_count 检索 superseded memory；借鉴 Graphiti/Zep 的 temporal validity、Memobase 的 event/profile timeline 和 Mnemis 的结构化枚举，但 derived memory 仍只做召回/组织，最终答案必须回到 raw evidence。
- `stage1_route_validity_v8_cached.json`：组合消融，把 v6 的 temporal route priority 与 v7 的 validity/superseded retrieval 合并；目的是验证两个 clean 通用改动是否互补，仍不使用 gold、category、judge、样本 id 或测试反馈。
- `stage1_evidence_arbitration_v9_cached.json`：query-side compiler ablation，基于 v7 增加 role-aware snippets、证据行标号和末尾 answer checklist；借鉴 Hindsight 的事实/推断分离、SimpleMem 的 token-density、Mnemis 的枚举覆盖和 Graphiti/Zep 的 provenance，但只改变证据组织，不使用任何离线标签或反馈。
- `stage1_compact_evidence_v10_cached.json`：query-side compact evidence ablation，吸收 v9 的 multi-session 正向信号，但关闭末尾 checklist、降低 snippet 长度和 evidence 行数，目标是在 6K query token 内提高证据覆盖。
- `stage1_selective_list_expansion_v11_cached.json`：query-side selective expansion ablation，默认保持 v7，仅对 question-text router 得到的通用 `list_count` information need 使用受限 role-aware snippet 扩展；目标是在 6K 附近保留 v10 的聚合题收益，同时避免 profile/temporal/assistant 噪声。

新增配置必须满足：

- 不使用 gold answer、judge output、benchmark label、sample id、qid、row index 或 test feedback。
- 关键开关显式写入配置，便于 ablation。
- 如果只是一次负向诊断，不长期保留配置文件；结论写入 `experiments/README.md` 或对应实验记录即可。
