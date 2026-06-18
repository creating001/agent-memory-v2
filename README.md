# Agent-Memory

本项目目标是构建一个通用、clean、可消融、可持续迭代的 Agent Memory 系统，并在 LongMemEval-S full 和 LoCoMo non-adversarial full 上用 judge accuracy 验证效果。

核心不是固定某个框架，而是在严格 clean setting 和成本约束下，持续提升长期记忆的 build、management、retrieval、context organization 和 answer 能力。方法可以迭代替换，但不能使用 gold answer、judge output、benchmark 标签、sample id、test feedback 或样本级规则。

## 当前 LTS 配置

默认配置：`configs/stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json`。Backbone 为 `Qwen/Qwen3.6-35B-A3B` no-thinking，build `max_tokens=4096`，answer `max_output_tokens=16384`。

| Benchmark | 当前 v125 local LTS | 说明 |
|---|---:|---|
| LongMemEval-S full | strict/lenient `0.812000 / 0.834000` | 兼容性继承；v125 LME dry-run `0/500` prompt/row change，v121 guard 在 v116 finalizer-applied 8 条上输出一致，不是新的 full rerun。 |
| LoCoMo non-adversarial full | strict/lenient `0.789610 / 0.807792` | route-only isolated artifact。 |

v125 的 LTS 理由：降低 goal 风险 #4 mechanical finalizer，并部分降低 #3 selected-context heuristic；#1 granularity/profile、#2 top-k/context noise/rerank、#5 build-memory organization 仍是优先待办。详细证据见 `experiments/README.md` 和 `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lts_promotion.md`。

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
