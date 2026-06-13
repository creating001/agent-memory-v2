# stage1_operation_workpad_v27_lme_s_full_ca4959c

## 目的

验证一个 query-side compiler 消融：在 v18 的 build-stage typed memory、dense+BM25 hybrid retrieval、raw evidence compiler 和 temporal/structured row guide 不变的前提下，关闭 v26 的结构化答案输出契约，改为只在 `list_count` 和 `temporal_lookup` 信息需求上加入私有 operation workpad。该 workpad 要求模型在内部检查答案槽位、候选证据是否覆盖目标实体/动作/时间范围、计数是否去重、日期是否来自事件文本而不只是 row Date；最终输出 schema 仍保持 `{reasoning, answer}`，不要求输出 `evidence_items`。

设计参考来自 `docs/method.md` 中的 query-time evidence compiler、procedural memory 和 external naive reader 思路，并借鉴了 LongMemEval 官方 con-style reader、creating001 的 evidence-first query 结构、SimpleMem/Hindsight/Memento 的通用流程记忆。取舍是：不迁移 creating001 中的 benchmark/字符串规则和 finalizer，只保留通用的“先读证据再完成集合/时间操作”的 reader discipline。

## 范围

- benchmark: LongMemEval-S
- subset: full
- samples: 500
- run kind: formal
- config: `configs/stage1_operation_workpad_v27_cached.json`
- prediction output: `outputs/formal/stage1_operation_workpad_v27_lme_s_full_ca4959c/predictions.jsonl`
- traces: `outputs/formal/stage1_operation_workpad_v27_lme_s_full_ca4959c/traces.jsonl`
- judge output: `experiments/formal/stage1_operation_workpad_v27_lme_s_full_ca4959c/deepseek_judge.json`
- evidence/source diagnostic: `experiments/formal/stage1_operation_workpad_v27_lme_s_full_ca4959c/evidence_recall.json`

## Git 与 Clean 状态

- prediction commit: `ca4959ce3a589ef8e077b7040960ace434e8543e`
- prediction dirty: `false`
- judge/evidence diagnostic commit: `ca4959ce3a589ef8e077b7040960ace434e8543e`
- judge/evidence diagnostic dirty: `true`，原因是本实验目录在预测后新增了 judge、diagnosis 和 comparison 文件。
- clean note: 预测流程没有读取 gold answer、judge output、benchmark label、question_type、sample id、qid 或 row index。DeepSeek judge 与 evidence/source coverage 只在预测完成后离线运行，输出不得进入 retrieval、compiler、answer 或 verifier。

## 结果

- DeepSeek judge accuracy: `0.742` (`371/500`)
- LME baseline target: `>= 0.800`
- 与 v18 对比: v18 `0.732`，v27 净增 `+5` correct
- 与 v26 对比: v26 `0.746`，v27 净减 `-2` correct
- avg build tokens: `80346.246`
- avg query tokens: `5259.276`
- token 预算: LME build `<=300K`、query `<=6K`，本次满足主线预算
- avg compiled evidence items: `34.058`
- avg build memory records: `129.662`
- avg active build memory records: `116.492`
- build cache hits/misses/writes: `3341/0/0`
- answer max input/output: `131072/16384`
- answer cache hits/misses/writes: `0/500/500`
- evidence/source coverage diagnostic: `1.0`，这不是主指标，只说明参考来源 session 被带入上下文。

## 分类型 Accuracy

| type | v18 | v26 | v27 |
|---|---:|---:|---:|
| knowledge-update | 0.821 | 0.731 | 0.808 |
| multi-session | 0.556 | 0.654 | 0.571 |
| single-session-assistant | 0.929 | 0.929 | 0.964 |
| single-session-preference | 0.367 | 0.300 | 0.500 |
| single-session-user | 0.943 | 0.900 | 0.871 |
| temporal-reasoning | 0.744 | 0.789 | 0.767 |

## 结论

v27 不是当前主线方向。它比 v18 略好，但低于 v26，且明显没有达到 LongMemEval-S full 的 80% baseline target。operation workpad 恢复了一部分 preference 和 knowledge-update 表现，但丢掉了 v26 在 multi-session/list 题上的主要收益；这说明问题不是简单把结构化输出契约改成私有提示就能解决。

因此本次不继续跑 LoCoMo full，避免把一个没有超过 LME 当前最好结果、且离 target 仍较远的方法扩展到昂贵全量评测。下一步应该回到更强的 evidence compiler / reader 结构，或者 build-stage typed memory 管理，而不是继续堆叠 answer-side prompt 小规则。
