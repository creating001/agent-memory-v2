# stage1_temporal_mention_time_fallback_v194 LTS summary

## Decision

V194 replaces v193 as the current local LTS.

V194 inherits v193 and adds a narrow prompt-side `mention_time_fallback` inside Event-Time Candidate Map. The fallback appears only when a low-coverage `exact_today` candidate is present and a stronger `mention_time_only` source row matches the question slot. It does not open broad relative-phrase candidates and still requires final verification in raw Memory Context.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, query-time route, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, or cache construction.
- Answer cache seeding used prediction-time traces and predictions only; no labels or judge outputs were read.

## Full Verification

| Benchmark | v194 vs v193 prompt diff | v194 vs v193 answer diff | v194 answer cache | Inherited judge accuracy |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `1/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

The only LoCoMo prompt change is `acae332af0e2a71091b4c697`:

- Question: `When did Nate take time off to chill with his pets?`
- v193 answer: `2022-08-22`
- v194 answer: `2022-08-22`
- v194 adds Memory 1 as `time_kind=mention_time_fallback`, `event_time=2022-08-22`, coverage `0.833`, alongside the weaker exact-today candidate coverage `0.667`.

## Why This Is LTS

V193 exposed a residual risk: a low-coverage `exact_today` prompt candidate could appear without showing the stronger target row that only had mention time. V194 reduces that risk by adding a source-backed, higher-coverage fallback only under that conflict pattern. It preserves all full-set answers and therefore inherits v193/v191/v184 judge accuracy.

## Artifacts

- Config: `configs/stage1_temporal_mention_time_fallback_v194_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `45390945d8154f01e5927957573180d3a3684516`
- Activation probe: `experiments/diagnostic/stage1_temporal_mention_time_fallback_v194_activation_probe/`
- LME full: `experiments/diagnostic/stage1_temporal_mention_time_fallback_v194_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_temporal_mention_time_fallback_v194_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_temporal_mention_time_fallback_v194_*`

## Next

- Continue using v193/v194 audit traces to design conflict-aware temporal activation beyond mention-time fallback.
- Keep broad visible candidate maps rejected unless they can prove changed-answer judge safety.
- Next target remains #2/#3: context organization and selected-context generality without hard pruning useful evidence.
