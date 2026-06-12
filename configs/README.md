# 配置入口

当前只保留主线需要的配置：

- `stage1_clean_skeleton.json`：无 LLM smoke / 单元测试级骨架配置。
- `stage1_strict_cached.json`：Stage-1 strict baseline，带 embedding cache。
- `stage1_route_guidance_cached.json`：ablation 配置，在 strict baseline 上增加通用 route guidance。
- `stage1_build_memory_cached.json`：当前主线候选，增加 build-stage LLM typed memory、memory cache、typed-memory retrieval 和 route guidance。
- `stage1_query_retrieval_v2_cached.json`：query-side ablation，复用 `stage1_build_memory_cached` 的 cold build cache，只改通用 stopword filtering、evidence ordering 和 temporal hints。
- `stage1_memory_compiler_v3_cached.json`：query-side memory compiler ablation，在 v2 上增加 typed memory sections 和 question-overlap memory ordering，继续复用 cold build cache。
- `stage1_temporal_preference_v4_cached.json`：query-side ablation，在 v3 上增加通用 temporal calculation workpad 和 personalized recommendation route，借鉴 SimpleMem 的 intent-aware retrieval、Zep/Graphiti 的 temporal validity 思路，以及 Memobase/Hindsight 的 profile/preference 分离；仍只使用问题文本、问题时间、raw evidence 和 build memory，不使用任何标签或样本级规则。
- `stage1_temporal_preference_v4_1_cached.json`：query-side ablation，在 v4 上把 temporal workpad 收紧到确实需要 duration / ago / between / order 计算的 temporal/current 问题，并限制 workpad 行数和 pairwise gap 数，目标是降低 token 成本和 multi-session 噪声。

新增配置必须满足：

- 不使用 gold answer、judge output、benchmark label、sample id、qid、row index 或 test feedback。
- 关键开关显式写入配置，便于 ablation。
- 如果只是一次负向诊断，不长期保留配置文件；结论写入 `experiments/README.md` 或对应实验记录即可。
