# V184 Strict Event-Time Candidate Map LTS Promotion

## Conclusion

V184 is promoted as the new local LTS.

It keeps v181's trace-only grouped event-time candidate manifest and adds a very narrow prompt-side Event-Time Candidate Map. The prompt map activates only for high-confidence source-backed exact/explicit event-date candidates after stripping selected-context timestamp wrappers, and the evaluation uses a seeded v181 answer cache so prompt-identical rows inherit v181 answers.

## Clean Setting

- Method config: `configs/stage1_strict_event_time_candidate_map_v184_seeded_qwen36_no_think_build4k_cached.json`.
- Method commits:
  - `f15cd24` added strict event-time candidate map gates.
  - `b56215b` added the seeded-cache v184 config.
- Full validation commits:
  - LME full run at `9f6160f`, dirty false.
  - LoCoMo full run at `4238ccf`, dirty false.
- Cache seed source: v181 full prediction traces and predictions only.
- No gold answers, judge outputs, benchmark labels, sample ids, test feedback, or sample-level rules are used by prediction, retrieval, compiler, answer, repair, finalizer, or cache construction.

## Full Results

| Benchmark | v184 strict/lenient | v181 strict/lenient | Evidence |
|---|---:|---:|---|
| LongMemEval-S full | `0.834000 / 0.846000` | `0.834000 / 0.846000` | answer diff `0/500`; map applied `0/500`; answer cache `500/0/0` |
| LoCoMo non-adversarial full | `0.793506 / 0.818831` | `0.792857 / 0.818182` | answer diff `2/1540`; map applied `3/1540`; answer cache `1538/2/2`; changed-answer dual judge `1/2 -> 2/2` |

LoCoMo derived counts:

- strict: `1221/1540 -> 1222/1540`.
- lenient: `1260/1540 -> 1261/1540`.

## Changed-Answer Judge

LoCoMo changed rows:

| record_key | v181 | v184 | dual judge transition |
|---|---|---|---|
| `f32506eabf8b9384df950965` | `June 20, 2023` | `2023-06-20` | correct -> correct |
| `acae332af0e2a71091b4c697` | `2022-08-27 to 2022-08-28` | `2022-08-22` | wrong -> correct |

Judge artifacts are in `diagnostic/stage1_strict_event_time_candidate_map_v184_full_changed_vs_v181/`.

## Risk Assessment

V184 reduces #5 risk relative to v181 by turning the grouped event-time management view into a guarded query-time activation mechanism for a tiny number of high-confidence exact/explicit date cases. It also avoids the v182 failure mode by:

- stripping selected-context wrapper timestamps before event-time extraction;
- disallowing relative/vague event-time candidates in the prompt map;
- disabling time-of-day question activation;
- using seeded cache evaluation so prompt-identical rows do not create answer regeneration noise.

Residual risk remains: all three LoCoMo map activations were `exact_today` candidates, and two were semantically noisy even though paired judge was non-negative. The next iteration should tighten `exact_today` activation or require stronger slot/action coverage.

## Outputs

- LME full experiment: `diagnostic/stage1_strict_event_time_candidate_map_v184_lme_s_full/`.
- LoCoMo full experiment: `diagnostic/stage1_strict_event_time_candidate_map_v184_locomo_nonadv_full/`.
- Changed judge: `diagnostic/stage1_strict_event_time_candidate_map_v184_full_changed_vs_v181/`.
- Probe summary: `diagnostic/stage1_strict_event_time_candidate_map_v184_probe_summary.md`.
