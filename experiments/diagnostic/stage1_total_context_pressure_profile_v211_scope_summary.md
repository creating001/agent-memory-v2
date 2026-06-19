# stage1_total_context_pressure_profile_v211 LTS summary

## Decision

V211 replaces v209 as the current local LTS.

V211 keeps v209's prediction behavior and judge accuracy, but removes the remaining average-turn-length `long_turn_precision` selector. The long-context profile is now selected by total raw context pressure: `min_total_chars=120000`.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or selector thresholds.
- The new selector uses only prediction-time raw dialogue size. It does not inspect answer text, labels, judge results, benchmark names, or sample ids.

## Method

- Parent LTS: `configs/stage1_conservative_context_budget_v209_seeded_qwen36_no_think_build4k_cached.json`
- New LTS: `configs/stage1_total_context_pressure_profile_v211_seeded_qwen36_no_think_build4k_cached.json`
- Profile name changes from `long_turn_precision` to `long_context_pressure`.
- Selector changes from `min_avg_turn_chars=300` to `min_total_chars=120000`.
- Retrieval, selected-context, compiler, answer, repair, finalizer, build memory, caches, context budget, and output style are otherwise unchanged from v209.

This is a risk-reduction LTS. It does not claim new accuracy. It reduces #1 by tying the long-context policy to general context pressure rather than average turn granularity.

## Full Verification

| Benchmark | answer diff vs v209 | route diff | prompt diff | evidence rows diff | retrieval hits diff | effective selected-context diff | profile selected | answer cache | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `500/500` via `long_context_pressure` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Trace-only differences:

- LongMemEval-S: `compiler_profile`, profile name, and audit risk reason differ on `500/500`, as intended.
- LoCoMo: profile remains unselected, so profile trace fields are unchanged except the audit selector label now reports `profile_thresholds`.

Token accounting is unchanged from v209:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

Because both full predictions are answer-identical to v209, v211 inherits the v209/v207/v206 dual DeepSeek flash judge records. No changed-answer judge is needed.

## Why This Is LTS

V211 is safer than v209 for #1 because it removes the last behavior-affecting avg-turn-length granularity selector from the current LTS. The replacement is still explicit and auditable, but it is based on total raw context pressure, which is a general system property.

Residual risks remain:

- #2: v211 does not reduce final prompt/query tokens. v210 showed tail snippets reduce tokens but hurt changed-answer judge accuracy.
- #3: selected-context still needs a safer source-backed organization path before further prompt-visible changes.
- #5: typed memory remains source-backed activation/organization support; broader memory lifecycle/state reasoning still needs improvement.

## Artifacts

- Method commit: `4115fe6f9914ae48577fbce81041415ada053378`
- LME evidence commit: `08cb5eb21529b821e83048415d68e3a0e1b17548`
- LME full: `experiments/diagnostic/stage1_total_context_pressure_profile_v211_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_total_context_pressure_profile_v211_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_total_context_pressure_profile_v211_*`

