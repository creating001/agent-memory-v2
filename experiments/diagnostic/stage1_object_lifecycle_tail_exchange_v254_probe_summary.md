# stage1_object_lifecycle_tail_exchange_v254_probe_summary

## 目的

验证 v254 scoped object-slot gate 是否在 probe50 上引入额外回退。v254 相对 v253 只新增两个可消融边界：advice/recommendation/resource-seeking query 不触发 object-slot activation，且 object-slot slot matching 忽略弱 overlap terms。

## 配置

- algorithm commit: `6a825d7`
- config: `configs/stage1_object_lifecycle_tail_exchange_v254_scoped_seeded_qwen36_no_think_build4k_cached.json`
- parent rejected candidate: `configs/stage1_object_lifecycle_tail_exchange_v253_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- clean boundary: prediction uses no labels, judge output, benchmark tags, sample ids, test feedback, gold answers, or sample-level rules.

## 验证

- `python -m py_compile src/memory/pipeline.py scripts/run_stage1.py src/tests/test_clean_skeleton.py`
- `python -m unittest discover -s src/tests`
- result: `323` tests passed.

## Probe 结果

| Benchmark | scope | object-slot applied | answer diff vs v250 | answer diff vs v253 | avg build/query tokens | changed dual judge |
|---|---:|---:|---:|---:|---:|---|
| LongMemEval-S | `50` | `4/50` | `1/50` | `0/50` | `86398.54 / 5678.68` | inherited v253 changed judge: strict/lenient `1/1 -> 1/1` |
| LoCoMo non-adversarial | `50` | `6/50` | `4/50` | `0/50` | `45868.00 / 6543.68` | inherited v253 changed judge: strict `1/4 -> 1/4`, lenient `1/4 -> 2/4` |

Trace diff:

- retrieval-order diff vs v250: `0/50` on both benchmarks.
- final-evidence diff vs v250: `0/50` on both benchmarks.
- new advice gate skipped count: `0/50` on both benchmarks; probe50 does not exercise the v253 full badcase class.

## 诊断

v254 probe is answer-identical to v253 because the first 50 examples do not include an object-slot activation that depends only on the newly ignored weak terms or the new advice/recommendation gate. This is still useful as a non-regression smoke check, but it is not enough for an LTS decision.

The required validation is full prediction plus changed-answer judge against v250/v253. In particular, the v253 full LME regression `39f2adfa686f1fa663896c83` should be blocked by the v254 advice/recommendation gate or weak-term filter before v254 can be considered safer than v253.

## 决策

v254 remains a full-candidate, not LTS. Run full prediction next with the committed v254 method state.

## 输出

- LME records: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v254_lme_probe50/`
- LME predictions/traces: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v254_lme_probe50/`
- LoCoMo records: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v254_locomo_probe50/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v254_locomo_probe50/`
