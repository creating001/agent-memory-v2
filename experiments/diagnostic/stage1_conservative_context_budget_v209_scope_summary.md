# stage1_conservative_context_budget_v209 LTS summary

## Decision

V209 replaces v207 as the current local LTS.

V209 is a conservative #2 top-k/context-noise cleanup. It keeps v207's answer, compiler prompt, evidence rows, finalizer, repair, and cache namespaces stable, but turns the context-budget audit into an actual retrieval budget with `22000` source characters, `32` protected/minimum anchors, and `max_hits=60`.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or budget gates.
- The budget is route-general across `current_state`, `fact_lookup`, `list_count`, `profile_preference`, and `temporal_lookup`.
- The budget preserves prompt/evidence coverage before LTS promotion; it is not tuned from judge feedback.

## Full Verification

| Benchmark | answer diff | route diff | prompt diff | evidence rows diff | retrieval hits diff | effective selected-context diff | context-budget dropped | answer cache | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `137/500` | `0/500` | `137` samples / `416` total / `0.832` avg | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0` samples / `0` total / `0.0` avg | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Context-budget audit prompt risk and selected-context risk are `0` on both full benchmarks.

Token accounting is unchanged from v207:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

Because both full predictions are answer-identical to v207, v209 inherits the v207/v206 dual DeepSeek flash judge records. No changed-answer judge is needed.

## Why This Is LTS

V209 is safer than v207 for #2 because it actually removes some long-tail retrieval candidates on LME while preserving the final prompt, evidence rows, selected-context materialization, answers, and token cost. V207 only proved the budget in trace; v209 applies a conservative version of it.

Residual risks remain:

- #1/#3: LME still relies on the `long_turn_precision` granularity profile; selected-context hard gates have previously hurt accuracy.
- #2: v209 does not reduce final prompt/query tokens yet. It reduces retrieval candidate noise before compilation.
- #5: broader memory organization and update reasoning still need more source-backed activations beyond status-like update pairs.

## Artifacts

- Config: `configs/stage1_conservative_context_budget_v209_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `7d604fa0b83a1608fbf967053cfa96822b2db0e9`
- LME evidence commit: `ca28f38259dc75a50bb3cef6c9b414fbafec531c`
- LME full: `experiments/diagnostic/stage1_conservative_context_budget_v209_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_conservative_context_budget_v209_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_conservative_context_budget_v209_*`

## Next

- Continue #2 toward prompt-stable context organization that also lowers final query tokens.
- Continue #1/#3 by replacing the remaining long-turn profile dependency with general route/context-pressure policies.
- Keep #5 source-backed: typed memory should activate raw evidence organization, not become independent answer evidence.
