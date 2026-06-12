# Diagnosis for formal/stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached

## 结论

v4 在 LoCoMo non-adversarial full 上达到 0.695906 DeepSeek judge accuracy，低于项目 LoCoMo mainline target 0.82。结果说明当前 raw + typed memory + session BM25 + temporal workpad 框架是有效底座，但还不足以稳定处理 LoCoMo 的时间、跨会话枚举和组合推理。

## 主要观察

- category 4 表现最好，704/841 = 0.837099，说明普通事实型召回和回答链路已经有可用基础。
- category 2 表现最差，135/321 = 0.420561；route 层的 temporal_lookup 也只有 146/338 = 0.431953。
- category 3 为 54/96 = 0.562500，且 evidence recall 仅 0.500000，是明显召回短板。
- list_count 为 70/131 = 0.534351，说明当前 top-k + session expansion 仍不擅长全局枚举和去重。
- fact_lookup 为 821/1017 = 0.807276，证明基础 retrieval/compiler 不是全局失效，后续应优先补时间和聚合能力。

## Evidence Recall

- overall: 0.831380 over 1536 rows with evidence labels
- category 1: 0.737589
- category 2: 0.862928
- category 3: 0.500000
- category 4: 0.887039

category 2 的 evidence recall 不低但 judge accuracy 很低，说明很多 temporal 错误不是简单漏召回，而是日期归一化、相对时间解释、事件时间与对话时间混用、以及 answer 阶段没有稳定使用时间证据。category 3 同时低召回和低准确率，后续需要更强的多证据组合检索。

## 典型错误模式

- 相对日期偏移：例如 gold 是 “the week before 9 June 2023”，prediction 直接输出 2023-06-09。
- 日期 off-by-one 或事件日期混用：例如 gold 是 7 May 2023，prediction 输出 2023-05-08。
- 只回答模糊来源而缺少关键实体：例如 gold 是 Sweden，prediction 只说 home country。
- 反事实或组合题用单条证据直接回答：例如 “Would Caroline still want...” 这类题需要组合支持经历和职业动机。
- list/count 题缺少全局覆盖和去重，当前召回深度不足以保证完整列表。

## 成本诊断

- avg query tokens 4420.572，低于 6K 主线预算。
- avg build tokens 2965.958，远低于 LoCoMo 100K 主线预算；但 build cache 不是全命中，miss/write 为 632。
- answer max output 已按协议设置为 16384；本次最大 query tokens 为 5278，没有触及 8K expensive 线。
- build 最大样本 tokens 为 65895，仍低于 100K 默认预算。

## 下一步建议

下一阶段应做 build-side 和 compiler-side 的通用改进，而不是基于 LoCoMo category 或样本规则调 route。

优先方向：

- Temporal state memory：借鉴 Graphiti/Zep 的 valid time / invalid time / supersede 思路，但保持轻量，不引入图数据库；每条 state/fact/event 保留 source_ids 和 timestamp。
- Time normalization：借鉴 SimpleMem 的时间归一化，把 “the week before X”、“Sunday before X”、“four years ago” 这类相对时间解析成可比较候选，同时保留原文证据。
- Profile/event separation：借鉴 LangMem 和 Memobase，把稳定 profile、偏好、一次性 event 分开，避免 profile 抽象覆盖原始事件。
- Multi-evidence aggregation：借鉴 MemMachine 和 Mnemis 的 raw episode + expansion / hierarchical traversal，对 list/count/category 3 这类题做更强的会话级和实体级覆盖。
- Compiler workpad：把 temporal workpad 从简单提示升级为可见的时间候选表和冲突链，但仍只使用 question text、question time、raw turns 和 build memory。

必须做的 ablation：

- v4 current baseline
- temporal normalization on/off
- temporal state memory on/off
- list/entity expansion on/off
- profile/event split on/off

所有新增模块必须保留 config 开关，正式实验继续记录 commit、dirty、token 成本、cache 命中、outputs 路径和 DeepSeek judge accuracy。
