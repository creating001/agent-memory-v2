# stage1_graph_evidence_overflow_v263_scope_summary

## 目的

验证 v263 的 bounded graph overflow 是否能让 v262 的 source-backed graph utility 真正进入 candidate/evidence selection，同时保持 clean setting、低 query 成本和 full accuracy 不回退。

v263 只新增 `retrieval.graph_utility.fusion_mode=overflow_tail_rescue` 和 `overflow_max_hits=4`。Graph utility 仍只读取 build-stage typed memory records、question、route、candidate source ids 和 raw source ids；输出仍是 raw source rows。它不读取 gold answer、judge output、benchmark label、sample id、row index 或 test feedback。

## 配置

- config: `configs/stage1_graph_evidence_overflow_v263_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_graph_evidence_utility_v262_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `8e793d4`
- changed-answer judge dir: `outputs/diagnostic/stage1_graph_evidence_overflow_v263_lme_changed_vs_v262/`

## Full Diff

| Benchmark | answer diff vs v262 | prompt diff | final-evidence diff | retrieval hits diff | token diff |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `15/500` | `33/500` | `33/500` | `0/500` | `33/500` |
| LoCoMo non-adversarial | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` |

Token / cache:

| Benchmark | avg build tokens | avg query tokens | answer cache hit/miss/write | graph utility applied |
|---|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6405.278` | `469/31/31` | `341/500` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.017532467533` | `1540/0/0` | `1373/1540` |

## Changed-Answer Judge

Dual `deepseek-v4-flash` judge on the 15 LongMemEval-S answers changed vs v262:

| Subset | strict | lenient |
|---|---:|---:|
| v262 changed subset | `9/15` | `9/15` |
| v263 changed subset | `7/15` | `8/15` |
| delta | `-2` | `-1` |

Derived full LongMemEval-S accuracy would be strict/lenient `0.828000 / 0.842000`, down from v262 `0.832000 / 0.844000`. LoCoMo is answer-identical and would inherit v262.

## 诊断

- v263 achieved the intended mechanical effect: graph utility overflow changed `turn_hits` on all graph-applied LME rows and changed final evidence on 33 LME rows.
- The behavior is too broad. Even a tail-only overflow can introduce distracting source rows when context budget drops other tail rows, causing answer changes and net LME judge regression.
- LoCoMo stayed answer-identical because overflow did not change final prompt/evidence there, so it gives no compensating gain.
- This is a clean negative result: source-backed graph utility is useful as an audit/selector interface, but overflow needs a stronger utility gate than "novel source from matched slot".

## 决策

v263 不升 LTS。当前 LTS 维持 v262。

下一版不应 simply increase overflow. Safer directions:

- restrict graph overflow to slots with explicit lifecycle conflict or supersede signals;
- require evidence pressure, e.g. context budget dropped rows from the same slot/session before adding graph overflow;
- prefer diagnostic ranking/feature logging before behavior-affecting source insertion;
- if any answer changes, run changed-answer dual judge before LTS.

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_graph_evidence_overflow_v263_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_graph_evidence_overflow_v263_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_graph_evidence_overflow_v263_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_graph_evidence_overflow_v263_locomo_full/`
- changed-answer judge: `outputs/diagnostic/stage1_graph_evidence_overflow_v263_lme_changed_vs_v262/`
