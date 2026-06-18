# v170 Source Value Specificity Guard

## Method

v170 inherits v169 and adds a narrow source-grounded finalizer guard:
when the draft answer is a short substring of exactly one support `value` in
the answer model's own prediction-time `evidence_report`, the finalizer
preserves the more specific source-backed value.

Examples:

- `aptitude test` -> `military aptitude test`
- `positive reinforcement` -> `positive reinforcement techniques`

The guard rejects count/date/duration/money/sum/average/order questions,
current/previous/latest/before/after/first/recent questions, and questions with
`or`. It also requires a single unique support value, rejects vague support
values, and does not use `reason` text as an answer source.

## Clean Protocol

- Prediction uses only question text, raw Memory Context, build memory, and the
  answer model's prediction-time structured response.
- No gold answer, judge output, benchmark label, sample id, test feedback, or
  sample-level rule is used by the guard.
- The guard does not compute a new value or merge multiple evidence items; it
  only preserves a more specific value already emitted by the answer model as a
  support item.
- Answer/build/repair prompts are unchanged from v169, so v170 intentionally
  reuses parent caches.

## Metrics

| Benchmark | Result |
|---|---|
| LongMemEval-S full | v170 vs v169 answer diff `0/500`; inherits strict/lenient `414/500` / `419/500` = `0.828000 / 0.838000` |
| LoCoMo non-adversarial full | v170 vs v169 answer diff `8/1540`; changed-answer paired dual judge strict `6/8 -> 7/8`, lenient `7/8 -> 7/8`; patched full strict/lenient `1217/1540` / `1256/1540` = `0.790260 / 0.815584` |

Changed-set judge detail:

- Positive strict-only improvement: `0d560e34c793d0dba1840fd8`, `aptitude test`
  -> `military aptitude test`, strict `false -> true`, lenient `true -> true`.
- No strict/lenient regressions on the 9 changed-answer records.
- One wrong answer remains wrong: `Japan` -> `Japan (Tokyo)` for a question whose
  gold answer is `United States`; the guard preserves source specificity but
  cannot fix retrieval/selection choosing the wrong country.

## Replay Verification

- LME prediction replay: answer cache `500/500` hits, build cache misses `0`,
  repair cache misses `0`, finalizer applied `1/500` from inherited v169 numeric
  slot label guard.
- LoCoMo prediction replay: answer cache `1540/1540` hits, build cache misses
  `0`, repair cache misses `0`, source value specificity guard applied `8/1540`.
- Token costs are inherited logically from v169: LME avg build/query
  `85393.566 / 6239.336`; LoCoMo avg build/query
  `62015.574026 / 6047.909091`.

## Risk Assessment

- Reduced: #4 answer-surface/source-grounded guardrail risk. v169 only protected
  a numeric `level` slot; v170 generalizes the same idea to short answers that
  lose a source-backed specificity modifier.
- Partially reduced: #5 query-time memory use. The answer model's structured
  memory report now participates in final answer organization, while typed
  memory remains source-backed activation/trace rather than independent
  evidence.
- Not solved: #1 granularity/profile design risk, #2 top-k/context noise and
  rerank/context organization, #3 selected-context generalization, and broader
  #5 lifecycle/update/conflict reasoning.
- Rejected nearby candidate: broad list completion from `evidence_report`
  triggered dozens of LoCoMo answers and over-expanded sum/order/current-state
  questions, so it was not implemented.

## Paths

- Config: `configs/stage1_source_value_specificity_guard_v170_qwen36_no_think_build4k_cached.json`
- LME predictions/traces: `outputs/diagnostic/stage1_source_value_specificity_guard_v170_lme_s_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_source_value_specificity_guard_v170_locomo_nonadv_full/`
- Changed-answer judge: `experiments/diagnostic/stage1_source_value_specificity_guard_v170_changed_vs_v169/`
- Full replay records:
  - `experiments/diagnostic/stage1_source_value_specificity_guard_v170_lme_s_full/`
  - `experiments/diagnostic/stage1_source_value_specificity_guard_v170_locomo_nonadv_full/`
