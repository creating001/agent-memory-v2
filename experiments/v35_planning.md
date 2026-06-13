# v35 Answer Format Guard Planning

## 背景

v34 route-budgeted retrieval 是当前 LoCoMo 最好结果：

- valid-only accuracy: `0.7797270955165692`
- invalid-as-wrong accuracy: `1200/1540 = 0.7792207792207793`
- 距 0.78 target 还差 `2` 条。

v34-v33 badcase 显示，下一步不应继续盲目改 retrieval。两个更小、更 general 的 query-side 问题值得先修：

1. `json_answer` 偶尔返回完整 JSON 字符串作为最终答案。v34 中有 `4` 条 JSON-like answers，其中 `2` 条 wrong；至少 `1` 条存在可通用抽取的 `"answer"` 字段。
2. duration 题偶尔输出小数周，如 `2.29 weeks`、`3.43 weeks`。v34 中这类答案有 `2` 条，均为 wrong，且问题都是通用 `How many weeks ...`。

## 方法设计

新增 `configs/stage1_answer_format_guard_v35_cached.json`：

- retrieval/build/compiler 完全沿用 v34。
- answer LLM 设置仍为 max input/output `131072/16384`。
- `CachedAnswerer` 对 `json_answer` cache hit 也从 `raw_response.content` 重新解析，避免 seeded cache 固化旧 parser 错误。
- `json_answer` parser 在 JSON 解析失败时，通用 salvage 最后一个 `"answer": "..."` 字段。
- finalizer 新增可关闭开关 `enable_duration_rounding_correction`：
  - 只在 question text 匹配 `how many days/weeks/months/years` 时启用。
  - 只处理单独的小数 duration answer，如 `2.29 weeks`。
  - 输出四舍五入后的整数单位，如 `2 weeks`。

这些逻辑只使用 prediction-time artifacts：question、draft answer、raw response/cache。它不读取 gold、judge、benchmark label、sample id、category、question_type、evidence label 或 test feedback。

## 外部方法借鉴和取舍

- creating001-agent-memory：借鉴其重视最终答案可读性和短答案抽取，但不迁移任何 benchmark-specific guardrail。
- SimpleMem answer_generator：借鉴 structured answer context 后需要稳定抽取 final answer 的思想。
- `docs/method.md`：对应 answer/verifier 与 compiler 后处理路线；本轮只做低风险 answer formatting，不引入新 retrieval 或 build memory。

## Gate 计划

v35 是 query-side parser/finalizer 修复，不需要重新 build。先做 no-LLM full prediction gate：

- 从 v34 full traces 预热 v35 answer cache。
- 运行 LoCoMo non-adversarial full prediction。
- 期望 answer cache 全命中或接近全命中，build/embedding cache 全命中。
- 检查：
  - avg build/query tokens 仍按 logical usage 统计；
  - finalizer applied count 是否等于预期小范围；
  - JSON-like final answers 是否减少；
  - duration decimal answers 是否减少；
  - token budget 不超标。

只有 gate 显示预测输出确实发生预期的小范围变化，再跑 DeepSeek judge。若只改变 2-4 条，judge 成本可接受，但仍必须记录为 full formal result，不能只报告局部样例。
