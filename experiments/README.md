# 实验入口

`experiments/` 是人工查看正式结果和关键诊断的入口。当前目录保持精简：无用 smoke、小样本、旧 ablation 结果不长期保留。

## 主要指标

方法好坏主要看离线 DeepSeek judge accuracy。

- LongMemEval-S full：500 条。
- LoCoMo non-adversarial full：1540 条。

`exact / F1 / BLEU` 只作为低成本诊断，不作为方法选择依据。

## 当前主线

配置：

- `configs/stage1_build_memory_cached.json`

方法摘要：

- build 阶段由本地 Qwen LLM 从 raw dialogue 中构建 typed memory。
- memory 类型包括 event、fact、preference、profile、state、relationship、plan。
- memory manager 做 source/provenance 记录、去重、轻量 supersede、active/superseded 状态和 cache。
- query 阶段同时检索 raw turns、session context 和 typed memory。
- compiler 将 typed memory view 与 raw context 一起组织给 answer model。
- DeepSeek judge 只在预测完成后离线使用。

外部方法借鉴与取舍：

- 借鉴 LangMem 的 collection/profile 思路。
- 借鉴 Memobase 的 profile/event timeline，但不删除 raw dialogue。
- 借鉴 MIRIX 的多类型 memory taxonomy，但不引入多 agent memory OS。
- 借鉴 MemMachine 的 raw episode + profile 辅助。
- 借鉴 Graphiti/Zep 的 temporal/provenance 思路，但暂不引入重型图数据库。

## 正式实验目录

正式全量实验使用：

```text
experiments/formal/<run_id>/
```

每个正式实验目录必须包含：

- `summary.md`
- `metrics.json`
- `diagnosis.md`
- `manifest.json`
- `config_snapshot.json`
- 离线 judge 结果
- 预测 outputs 路径

必须记录：

- git commit 和 dirty 状态
- config
- benchmark/subset
- token 成本，尤其 build/query tokens
- build memory cache、records、memory hits
- runner workers / 并行度
- outputs 路径
- accuracy-first 诊断结论

如果必须做子集，只能标成 diagnostic，并优先按 question-derived information need 分层采样；不能把前 N 条子集当正式结论。
