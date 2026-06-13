# v33 Retrieval Top-60 Planning

## 背景

v32 selective repair 在 LoCoMo full 上 token 合格，但 accuracy 与 v29 持平。关键诊断：

- repair triggered `263/1540`，applied `11/1540`，实际修改率太低。
- repair-applied 子集 fixed `3` / broken `1`，有局部正信号，但不足以推动 full accuracy。
- wrong case 中仍有相当比例的 gold evidence 没进入 compiled context：v32 wrong `367`，其中有 evidence labels 的 `366`，compiled hit `262`，约 `104` 个 wrong 仍是 retrieval/source coverage 缺口。

因此 v33 不继续扩大同 context repair，而是先做 non-LLM retrieval expansion：在不改 build memory 和 answer contract 的情况下，把 raw-turn dense+BM25 retrieval / compiler evidence budget 从 top-40 扩到 top-60。

## 外部方法借鉴

- SimpleMem：借鉴 planning/reflection retrieval 的思想，即 answer 前先提高信息覆盖；v33 先做保守版本，不加额外 LLM query planner，只扩大 hybrid retrieval candidate pool。
- DeepResearch / IterResearch：借鉴 completeness-before-answering，但 v33 不做多轮 agentic search，避免 query token 失控。
- creating001-agent-memory：借鉴其 clean naive RAG 中 top-k retrieval、Date/role/source formatting、evidence-first answer；舍弃 rule-heavy guardrails 和 benchmark route。
- `docs/method.md`：对应 multi-view retrieval、source expansion 和 evidence table 路线；实验必须报告 evidence recall、context size、query tokens 和 final accuracy。

## Retrieval-Only 诊断

run: `v33_retrieval_top60_null_locomo_full_a80816a`

该 run 使用 null answer，不调用 answer LLM；prediction 阶段不读取 labels/gold/judge/category/sample id。完成后离线读取 evidence labels 计算 recall。

对比 v32/v29 top-40：

- top40 evidence_recall: `0.8912760416666666`
- top60 evidence_recall: `0.91796875`
- top40 avg_context_chars: `11416.253896103895`
- top60 avg_context_chars: `15325.005844155845`
- top60 avg_evidence_items: `60.0`
- build cache hits/misses: `12411/0`
- embedding cache hits/misses: `7422/0`

按 route 的 evidence recall：

- fact_lookup: `0.8748768472906404 -> 0.9064039408866995`
- list_count: `0.8931297709923665 -> 0.916030534351145`
- profile_preference: `0.9166666666666666 -> 0.9583333333333334`
- temporal_lookup: `0.9349112426035503 -> 0.9467455621301775`
- current_state: `1.0 -> 1.0`

这个提升说明 top60 有足够理由进入 answer gate。

## 方法设计

新增 `configs/stage1_retrieval_top60_v33_cached.json`：

- build memory 与 v29 保持一致。
- route 与 v29 保持一致。
- retrieval:
  - `top_k=60`
  - `max_top_k=60`
  - dense `top_k=60`
  - dense `protect_top_n=48`
- compiler:
  - `max_evidence_items=60`
  - `max_evidence_chars=26000`
  - evidence_report 仍为 v29 的 compact contract，不启用 v31 detail。
- answer:
  - Qwen/Qwen3-30B-A3B-Instruct-2507
  - max input/output `131072/16384`
  - repair/finalizer 关闭，隔离 retrieval expansion 效果。

## Gate

先跑 20 条 no-label route-stratified answer gate：

- 检查 avg query tokens 是否 <= 6K。
- 检查 answer max input/output 是否 `131072/16384`。
- 检查 build cache、embedding cache 是否命中，build tokens 是否按 logical cold-build 统计。
- 不读取 labels/gold/judge/category/sample id。

如果 gate 通过，先跑 LoCoMo non-adversarial full。只有 LoCoMo accuracy 高于 v29/v32 且 token 合格，再考虑 LongMemEval-S full。

## 2026-06-14 Gate 结果

先跑了一个 mixed route-stratified probe，因包含 LongMemEval 长样本，avg query tokens `6483.5`，不适合作为 LoCoMo gate；该无用记录已删除。LongMemEval 如需验证 top60，必须单独做 LME gate 或增加 row truncation。

随后生成 LoCoMo-only route-stratified no-label probe：

- source: `outputs/prepare_locomo_non_adversarial/prediction_input.jsonl`
- sampling: first 4 examples per question-derived information_need route
- routes: fact_lookup、temporal_lookup、list_count、profile_preference、current_state 各 4 条
- clean: 不读取 labels/gold/judge/category/sample id；`record_key` 只留在 sampling manifest，不进入 pipeline。

LoCoMo-only gate run: `v33_top60_locomo_probe_65daf7d`

- samples: `20/20`
- avg build tokens: `44168.8`
- avg query tokens: `5287.0`
- query token min/max: `4447/6323`
- avg context chars: `15565.4`
- avg evidence items: `60.0`
- build cache hits/misses/writes: `123/0/0`
- answer cache hits/misses/writes: `0/20/20`
- answer max input/output: `131072/16384`

结论：v33 top60 通过 LoCoMo no-label/token gate，可以跑 LoCoMo non-adversarial full。暂不跑 LongMemEval，除非 LoCoMo full 正向且 LME 单独 gate 合格。

## 2026-06-14 LoCoMo Full 结果

run: `stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a`

- benchmark/subset: LoCoMo non-adversarial full
- samples: `1540`
- commit: `f016f9a7233172a6d3bb75f247a68cd1e8ec9556`
- dirty: prediction run 开始时仅有用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`；未发现预测代码或 v33 config 的未提交修改。
- answer max input/output: `131072/16384`
- avg build tokens: `58386.00779220779`
- avg query tokens: `5191.105844155844`
- total build tokens: `89914452`
- total query tokens: `7994303`
- judge tokens: `666030`
- build cache hits/misses/writes: `12411/0/0`
- embedding cache hits/misses/writes: `7422/0/0`
- answer cache hits/misses/writes: `31/1509/1509`
- avg compiled evidence items: `60.0`
- avg context chars: `15325.005844155845`

DeepSeek judge:

- valid-only accuracy: `0.7719298245614035`
- invalid-as-wrong accuracy: `1188/1540 = 0.7714285714285715`
- previous best v29/v32: `1173/1540 = 0.7616883116883116`
- net improvement: `+15` correct
- LoCoMo target gap: still short by about `14` correct examples.

Evidence recall:

- overall: `0.91796875`
- type 1: `0.925531914893617`
- type 2: `0.9190031152647975`
- type 3: `0.6956521739130435`
- type 4: `0.93935790725327`

v29 对照:

- both_correct: `1112`
- both_wrong: `291`
- gained: `76`
- lost: `61`
- fact_lookup net `+16`
- list_count net `+5`
- profile_preference net `+2`
- current_state net `+1`
- temporal_lookup net `-9`

结论：v33 证明扩大 retrieval/compiled evidence 对 LoCoMo 有真实正收益，但 temporal_lookup 不适合无差别扩大 context。下一轮不继续盲目堆 top-k，而是做 v34 route-budgeted retrieval：非 temporal route 保留 top60，temporal_lookup 回到更窄 top40/compile budget，仍只依赖 question-derived information_need，保持 general/clean。
