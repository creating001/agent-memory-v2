# 配置入口

当前只保留主线需要的配置：

- `stage1_clean_skeleton.json`：无 LLM smoke / 单元测试级骨架配置。
- `stage1_strict_cached.json`：Stage-1 strict baseline，带 embedding cache。
- `stage1_route_guidance_cached.json`：ablation 配置，在 strict baseline 上增加通用 route guidance。
- `stage1_build_memory_cached.json`：当前主线候选，增加 build-stage LLM typed memory、memory cache 和 typed-memory retrieval。

新增配置必须满足：

- 不使用 gold answer、judge output、benchmark label、sample id、qid、row index 或 test feedback。
- 关键开关显式写入配置，便于 ablation。
- 如果只是一次负向诊断，不长期保留配置文件；结论写入 `experiments/README.md` 或对应实验记录即可。
