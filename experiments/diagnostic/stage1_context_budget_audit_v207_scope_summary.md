# stage1_context_budget_audit_v207 LTS summary

## Decision

V207 replaces v206 as the current local LTS.

V207 is a trace-only #2 top-k/context-noise audit. It inherits v206 prediction behavior and adds a retrieval context-budget simulation that estimates whether a conservative 16k-character, 32-anchor budget would drop evidence currently visible in the prompt. The audit is recorded in traces and metrics only; it is not used by retrieval, compiler, answer, repair, finalizer, or cache keys.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or guide gates.
- The new audit only simulates a generic context-budget pressure policy over already retrieved hits. It does not prune, rerank, rewrite prompts, or change answers.
- The audit is route-scoped by information need and records projected dropped sources, prompt-row missing sources, selected-context missing sources, and a safe-for-current-prompt flag.

## Full Verification

| Benchmark | v207 vs v206 answer diff | route diff | prompt diff | evidence rows diff | retrieval hits diff | answer cache | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Because both full predictions are answer-identical to v206, v207 inherits the v206/v205/v204/v202 dual DeepSeek flash judge records. No changed-answer judge is needed for this promotion.

## Context-Budget Audit

| Benchmark | audit applied | avg candidates | avg projected returned | avg projected dropped | prompt risk | selected-context risk |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` | `40.0` | `37.75` | `2.25` | `0` | `0` |
| LoCoMo non-adversarial full | `1540/1540` | `55.61038961038961` | `55.61038961038961` | `0.0` | `0` | `0` |

The audit shows that this simulated budget would not remove any evidence row or selected-context row that the current compiler actually used. This lowers #2 risk by making budget pressure measurable before enabling real pruning or rerank-based filtering. It does not yet claim lower query tokens or solved context noise, because v207 is trace-only.

Token accounting from run summaries:

| Benchmark | avg build tokens | avg query tokens | avg context chars |
|---|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` | `19775.056` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` | `17402.64025974026` |

## Why This Is LTS

V207 is safer than v206 for #2 because it adds full-run observability for context-budget/rerank risk without changing prediction behavior. It gives the next real pruning or rerank experiment a concrete safety gate: do not drop prompt-visible evidence rows or selected-context rows unless a stronger replacement policy is verified.

Residual risks remain:

- #1/#3: LME still selects the `long_turn_precision` granularity profile; selected-context behavior still needs a more general policy.
- #2: token/query cost is not reduced yet; v207 only identifies a safe candidate budget surface.
- #5: v206's update-pair state guide remains narrow and safe, but broader memory organization/update reasoning still needs more positive source-backed activations.

## Artifacts

- Config: `configs/stage1_context_budget_audit_v207_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `91b0d14ff52decdd97d97919b6130931b800df2b`
- LME full: `experiments/diagnostic/stage1_context_budget_audit_v207_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_context_budget_audit_v207_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_context_budget_audit_v207_*`

## Next

- Convert the trace-only budget into a guarded behavior only if prompt-row and selected-context coverage stay safe on full runs.
- Explore rerank as a second-stage ordering signal under this audit, not as broad hard pruning.
- Continue #1/#3 cleanup by replacing the remaining long-turn profile dependency with general route/context-pressure policies.
