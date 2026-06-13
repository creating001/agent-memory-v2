# v34 Route-Budgeted Retrieval Planning

## 背景

v33 top-60 retrieval expansion 在 LoCoMo non-adversarial full 上取得当前最好结果：

- v33 invalid-as-wrong accuracy: `1188/1540 = 0.7714285714285715`
- v29/v32: `1173/1540 = 0.7616883116883116`
- net: `+15` correct
- evidence_recall: `0.91796875`，高于 top-40 的 `0.8912760416666666`

但 v33 的收益不是均匀的。离线 judge 对照显示：

- fact_lookup net `+16`
- list_count net `+5`
- profile_preference net `+2`
- current_state net `+1`
- temporal_lookup net `-9`

因此下一轮不能无差别继续扩大 context。v34 的目标是保留 v33 在非 temporal route 的覆盖收益，同时降低 temporal_lookup 的旧事实/竞争日期噪声。

## 外部方法借鉴和取舍

- SimpleMem：借鉴 hybrid retrieval 和 structured context 的覆盖优先思想；v34 不引入额外 LLM planner，避免 query token 失控。
- DeepResearch / IterResearch：借鉴 answer 前先补足证据的思路；v34 只做单轮、低成本 budget selection，不做多轮 agentic search。
- creating001-agent-memory：借鉴 query 组织和 temporal evidence-first 的经验；不迁移 rule-heavy guardrails、target phrase、category、sample id 或任何 benchmark 专门逻辑。
- `docs/method.md`：对应 multi-view retrieval、question-text router、evidence compiler 路线；route 只能来自 question text 的 generic information_need。

## 方法设计

新增 `configs/stage1_route_budgeted_retrieval_v34_cached.json`：

- build memory 与 v29/v33 保持一致。
- answer LLM 与输出限制保持协议：max input/output `131072/16384`。
- 非 temporal route 使用 v33 top-60：
  - retrieval `top_k=60`
  - dense `top_k=60`
  - dense protect `48`
  - compiler `max_evidence_items=60`
  - compiler `max_evidence_chars=26000`
- `temporal_lookup` 使用 v29 top-40：
  - retrieval route override `top_k=40`
  - retrieval route override `max_top_k=40`
  - dense route override `dense_top_k=40`
  - dense protect override `32`
  - compiler route override `max_evidence_items=40`
  - compiler route override `max_evidence_chars=18000`

该 route 只由 `QuestionRouter` 根据问题文本得到，不读取 LoCoMo category、LongMemEval question_type、gold、judge、evidence label、sample id 或 row index。

## 代码改动

- `Stage1Pipeline` 新增 `retrieval.route_overrides`，支持按 generic information_need 覆盖 `top_k/max_top_k/dense_top_k/lexical_protect_top_n/dense_protect_top_n`。
- `scripts/run_stage1.py` 记录 `retrieval.route_overrides`、`avg_effective_top_k`、`avg_effective_dense_top_k` 和 `avg_effective_dense_protect_top_n`。
- 单测验证 route override 来自 question-derived information_need，并拒绝隐藏标签名。

## Gate 计划

先跑 LoCoMo-only no-label route-stratified gate：

- source: `outputs/prepare_locomo_non_adversarial/prediction_input.jsonl`
- 每个 question-derived information_need route 采样 4 条，共 20 条。
- 不读取 labels/gold/judge/category/sample id；`record_key` 只允许 runner 做离线 join，不进入 pipeline。
- 检查：
  - avg query tokens <= `6000`
  - avg build tokens 按 logical cold-build 记录
  - answer max input/output `131072/16384`
  - build/embedding cache 正常
  - route overrides 生效，temporal_lookup effective top_k 为 40，非 temporal 为 60

如果 gate 合格，跑 LoCoMo non-adversarial full。只有 v34 LoCoMo full 高于 v33 且 token 合格，再考虑 LME；LME 必须单独 gate，因为 v33 mixed gate 显示 top-60 对 LME 长样本有超 6K 风险。

## 2026-06-14 Gate 结果

run: `v34_route_budgeted_probe_8ce3c3b`

- source: `outputs/diagnostic/v33_locomo_route_stratified_probe/prediction_input.jsonl`
- samples: `20`，每个 question-derived information_need route 4 条
- commit: `8ce3c3bf59dfef3d19dbdc48edba99c452bc78b8`
- dirty: 仅用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`
- workers: `8`
- answer max input/output: `131072/16384`
- avg build tokens: `44168.8`
- avg query tokens: `5050.0`
- avg effective top_k: `56.0`
- avg effective dense_top_k: `56.0`
- avg effective dense_protect_top_n: `44.8`
- avg compiled evidence items: `56.0`
- avg context chars: `14776.45`
- build cache hits/misses/writes: `123/0/0`
- embedding cache hits/misses/writes: `2051/0/0`
- answer cache hits/misses/writes: `0/20/20`

Route budget check:

- `temporal_lookup`: top_k `40`，dense_top_k `40`，dense_protect_top_n `32`，compiled evidence rows `40`
- `fact_lookup`: top_k `60`，dense_top_k `60`，dense_protect_top_n `48`，compiled evidence rows `60`
- `list_count`: top_k `60`，dense_top_k `60`，dense_protect_top_n `48`，compiled evidence rows `60`
- `profile_preference`: top_k `60`，dense_top_k `60`，dense_protect_top_n `48`，compiled evidence rows `60`
- `current_state`: top_k `60`，dense_top_k `60`，dense_protect_top_n `48`，compiled evidence rows `60`

结论：v34 通过 LoCoMo no-label/token gate，可以跑 LoCoMo non-adversarial full。暂不跑 LongMemEval-S full；如果 v34 LoCoMo full 超过 v33，再单独做 LME gate。
