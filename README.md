# Agent-Memory

本项目目标是构建一个通用、clean、且具有方法创新性的 Agent Memory 系统，并在 LongMemEval-S full 和 LoCoMo non-adversarial full 上用 judge accuracy 验证效果。

核心不是固定某个现成框架，也不是为 benchmark 编写专门规则，而是在严格 clean setting 和成本约束下，系统性探索长期记忆的 build、management、retrieval、context organization 和 answer 机制。我们希望方法不仅能取得更高性能，还能体现本项目在长期记忆建模上的独特思考，形成一套更可靠、更可解释、性能更强、更具泛化能力的 Agent Memory 框架。方法可以持续迭代和替换，但所有改动必须保持 general、clean 和可复现，不能使用 gold answer、judge output、benchmark 标签、sample id、test feedback 或样本级规则等。

## 当前 LTS 配置

默认配置：`configs/stage1_source_backed_lifecycle_memory_repair_v230_seeded_qwen36_no_think_build4k_cached.json`。Backbone 为 `Qwen/Qwen3.6-35B-A3B` no-thinking，build `max_tokens=4096`，answer `max_output_tokens=16384`。

| Benchmark | 当前 v230 local LTS | 说明 |
|---|---:|---|
| LongMemEval-S full | strict/lenient `0.834000 / 0.846000` | v230 与 v229 answer/prompt/evidence rows/retrieval hits diff `0/500`；source-backed state repair reason `4/500`，applied `0/500`；avg build/query tokens `85393.566 / 6682.852`。 |
| LoCoMo non-adversarial full | strict/lenient `0.793506 / 0.818831` | v230 与 v229 answer/prompt/evidence rows/retrieval hits diff `0/1540`；source-backed state repair reason `2/1540`，applied `0/1540`；guarded rerank applied `2/1540`；avg build/query tokens `62015.57402597403 / 6108.888311688312`。 |

v230 的 LTS 理由：继承 v229 的 full answer 和 judge accuracy，同时把 v225 的 #5 trace-only State/Update Organization Ledger 推进一步到 source-backed typed-memory repair-time verifier。它只在 current_state 且问题显式询问 current/previous/now/how-long 状态、draft 有多个 support values、raw lifecycle rows 足够、typed memory ledger 与问题对齐且 source-backed 时触发 repair；typed memory 只作为 Memory Context 原文行索引，不独立作证据。代价是少量 query token 增加。详细证据见 `experiments/README.md` 和 `experiments/diagnostic/stage1_source_backed_lifecycle_memory_repair_v230_scope_summary.md`。

## 目录

```text
docs/          规则、约束、架构和方法调研
src/           项目代码：common、data、memory、evaluation、tests
configs/       可消融配置
scripts/       数据准备、预测、评测、诊断脚本
experiments/   人类可读的 LTS / split best / 关键 baseline 实验记录
outputs/       保留实验的预测、trace、必要 cache 和数据准备产物
data/          本地数据入口，不提交大数据
external/      只读外部参考实现
```

## 必读文档

- `AGENTS.md`
- `docs/clean_protocol.md`
- `docs/constraints.md`
- `docs/experiment_protocol.md`
- `docs/architecture.md`
- `docs/method.md`

需要深入外部方法时再读 `docs/method_cards.md`。

## 本地检查

```bash
conda activate agent-memory
python -m pip install -e .
python -m unittest discover -s src/tests
```

每个算法版本先做本地 git commit，后续 dry-run、subset、judge 或分析记录引用该 commit。dirty 状态只用于如实说明当时工作区，不是重跑条件；不要为了让 manifest 变成 clean 反复重跑。

实验记录按用途分层：普通诊断/dry-run 只需记录目的、配置或 commit、关键 trace/metrics 结论和 outputs 路径；准备升 LTS、正式汇报、full/split best，或需要下性能结论的 run，才必须在 `experiments/` 下留下 summary、metrics、diagnosis、配置快照、token 成本和完整 outputs 路径。方法性能主指标是 DeepSeek dual flash judge accuracy：`deepseek-v4-flash` 独立跑两遍，strict 为两遍都判对，lenient 为任一遍判对；两遍 judge 均保持 temperature `0` 和 default thinking。Exact/F1/BLEU 只作参考。
