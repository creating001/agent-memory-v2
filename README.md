# Agent-Memory

本项目目标是构建一个通用、clean、且具有方法创新性的 Agent Memory 系统，并在 LongMemEval-S full 和 LoCoMo non-adversarial full 上用 judge accuracy 验证效果。

核心不是固定某个现成框架，也不是为 benchmark 编写专门规则，而是在严格 clean setting 和成本约束下，系统性探索长期记忆的 build、management、retrieval、context organization 和 answer 机制。我们希望方法不仅能取得更高性能，还能体现本项目在长期记忆建模上的独特思考，形成一套更可靠、更可解释、性能更强、更具泛化能力的 Agent Memory 框架。方法可以持续迭代和替换，但所有改动必须保持 general、clean 和可复现，不能使用 gold answer、judge output、benchmark 标签、sample id、test feedback 或样本级规则等。

## 当前 LTS 配置

默认配置：`configs/stage1_operation_overflow_preserved_source_chain_v307_query_restore_seeded_qwen36_no_think_build4k_cached.json`。Backbone 为 `Qwen/Qwen3.6-35B-A3B` no-thinking，build `max_tokens=4096`，answer `max_output_tokens=16384`。

| Benchmark | 当前 v307 local LTS |
|---|---:|
| LongMemEval-S full | strict/lenient `0.834000 / 0.846000`，avg build/query tokens `85393.566 / 6455.588` |
| LoCoMo non-adversarial full | strict/lenient `0.794156 / 0.819481`，avg build/query tokens `62015.57402597403 / 6093.87012987013` |

v307 的 LTS 理由：在 v305 source-chain coverage utility 基础上，修正 operation source expansion 的浅消费问题：guarded operation source 不再只停留在 trace selected/emitted，而是可以在已有 overflow hits 后进入 candidate pool 并接受 context-budget audit。Typed/derived memory 仍不能直接替代 raw evidence；operation plan 只能作为 source-backed context organization / coverage / verification signal。v307 的 LongMemEval-S full answer/prompt/evidence diff vs v306 为 `0`；LoCoMo 只有 `1/1540` changed output，v306/v307 changed dual judge 均 strict correct，因此 full accuracy 不退。详细证据见 `experiments/README.md` 和 `experiments/diagnostic/stage1_operation_overflow_preserved_source_chain_v307_full_summary.md`。

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

实验记录按用途分层：普通诊断/dry-run 只需记录目的、配置或 commit、关键 trace/metrics 结论和 outputs 路径；进入候选表、LTS 判断或算法性能结论的版本，必须报告 full dual judge accuracy（strict/lenient）、avg build tokens 和 avg query tokens。full 口径可以来自全量 judge，也可以来自 changed-output judge + 未变样本已有判定的合并指标；核心是结论可信、可复现、能服务方法目标，而不是为了继承或全量重跑本身。方法性能主指标是 DeepSeek dual flash judge accuracy：`deepseek-v4-flash` 独立跑两遍，strict 为两遍都判对，lenient 为任一遍判对；两遍 judge 均保持 temperature `0` 和 default thinking。Exact/F1/BLEU 只作参考。

本地运行 offline judge 时可以读取仓库根目录 `.env` 注入 API key，例如在单条命令子进程里 `source .env` 后执行 judge 脚本；但禁止打印、复制、写入实验记录或提交 `.env` 内容。`.env` 只能用于离线评测/外部服务认证，不能进入 prediction、retrieval、compiler、answer、verifier 或 cache build 逻辑。
