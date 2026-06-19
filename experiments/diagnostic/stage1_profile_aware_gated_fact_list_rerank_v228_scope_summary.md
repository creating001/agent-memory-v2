# stage1_profile_aware_gated_fact_list_rerank_v228 rejection summary

## Decision

V228 is rejected and does not replace v225 LTS.

V228 is clean and fixes v226/v227 scope problems, but full LoCoMo changed-answer judge is negative. Current LTS remains v225.

## Method

V228 inherits v225 and adds two retrieval controls for #2 context-noise reduction:

- `retrieval.route_override_precedence = before_profile`, so route overrides do not overwrite the `long_context_pressure` profile.
- `retrieval.rerank.min_effective_top_k = 56`, so fact/list rerank only expands the candidate pool when the effective pre-rerank top-k exposes a real tail.

When active, fact/list rerank keeps the first `52` retrieval anchors, selects the final `4` rows from a `60`-row pool with `Qwen/Qwen3-Reranker-0.6B`, and preserves original retrieval order.

## Full Prediction Diff

| Benchmark | prompt diff | evidence rows diff | retrieval hits diff | answer diff | rerank applied |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` |
| LoCoMo non-adversarial full | `779/1540` | `779/1540` | `882/1540` | `305/1540` | `1152/1540` |

## Cost

| Benchmark | avg build tokens | avg query tokens | rerank tokens |
|---|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6637.834` | `0` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6026.762987012987` | `16869852` |

Rerank model tokens are reported separately from build/query LLM visible tokens. V228 reduces LoCoMo visible query tokens modestly, but adds substantial rerank cost.

## Changed-Answer Judge

Dual `deepseek-v4-flash` judge on the `305` LoCoMo answers changed vs v225:

| Side | strict | lenient |
|---|---:|---:|
| v225 | `232/305` | `240/305` |
| v228 | `231/305` | `235/305` |
| delta | `-1` | `-5` |

Derived LoCoMo full accuracy would be strict/lenient `0.792857 / 0.815584` (`1221/1540`, `1256/1540`), below v225 `0.793506 / 0.818831` (`1222/1540`, `1261/1540`).

LongMemEval-S answer/prompt/evidence/retrieval diff is `0/500`, so LME accuracy would inherit v225. That does not offset the LoCoMo regression.

## Diagnosis

The profile-aware gate makes the method technically clean and scope-correct, but broad fact_lookup rerank is still too disruptive. It changes `779/882` fact_lookup prompts and improves some answers while regressing slightly more. The failure mode matches v223/v224: source/span preservation alone is not enough when the intervention broadly changes final evidence membership.

The next #2 attempt should not rerank all fact_lookup tails. It should use the v222/v225 pressure and source-flow ledgers to target only rows that are not protected by source-backed final evidence, local session chains, memory/source anchors, or question-term coverage.

## Artifacts

- Method commit: `6ec5529a93c81e78e7f4cb09ffef1cead93d70a1`
- Probe eval commit: `0abc2c4cb4d7988d38f710f28c25af150b5c272a`
- LME full eval commit: `348623c477e52e676e3c53e86033fc6e452dd916`
- Config: `configs/stage1_profile_aware_gated_fact_list_rerank_v228_seeded_qwen36_no_think_build4k_cached.json`
- LME full: `experiments/diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_locomo_nonadv_full/`
- Changed-answer judge outputs: `outputs/diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_full_changed_vs_v225/`
