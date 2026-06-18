# V125 temporal gain/loss badcase analysis

## Purpose

Diagnose the LoCoMo temporal-route paired judge changes for V125 against the current V116 LTS.

This is offline error analysis. It reads completed predictions, traces, gold answers, and judge outputs after prediction is finished. The findings must not be converted into sample-level prediction rules, benchmark-label rules, sample-id rules, or test-feedback-driven shortcuts.

## Inputs

- Paired judge comparison: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/paired_judge_comparison_vs_v116.json`
- V125 traces: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/traces.jsonl`
- V116 traces: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/traces.jsonl`
- V125 predictions: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/predictions.jsonl`
- V116 temporal subset predictions: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/v116_temporal_subset_predictions.jsonl`

## Accuracy-first summary

Primary metric is dual `deepseek-v4-flash` judge accuracy. Exact/F1/BLEU remain diagnostic only.

| scope | strict | lenient |
|---|---:|---:|
| V116 temporal subset | `0.772189` (`261/338`) | `0.786982` (`266/338`) |
| V125 temporal subset | `0.792899` (`268/338`) | `0.813609` (`275/338`) |
| paired gain/loss | `19/12`, net `+7` | `19/10`, net `+9` |

Changed answers:

- `132/338` answers changed.
- Strict buckets among changed answers: both correct `69`, both wrong `32`, gain `19`, loss `12`.
- Lenient buckets among changed answers: both correct `76`, both wrong `27`, gain `19`, loss `10`.
- Same normalized answer but changed judge label: lenient gain `1`, lenient loss `1`; strict gain `2`, strict loss `1`. These are mostly judge variance rather than method behavior.

## Trace mechanism

V125 does not change selected raw evidence row ids on the temporal subset. It changes row text for selected short temporal rows by materializing same-session local context.

For the changed-answer set:

| lenient bucket | n | avg context delta | avg query delta | V125 avg query | V125 query `>8K` |
|---|---:|---:|---:|---:|---:|
| gain | `19` | `+1702.211` chars | `+416.263` tokens | `5554.158` | `0` |
| loss | `10` | `+1717.800` chars | `+965.600` tokens | `7699.900` | `2` |
| both correct | `76` | `+1688.618` chars | `+323.197` tokens | `5359.816` | `0` |
| both wrong | `27` | `+1580.778` chars | `+7.111` tokens | `5722.593` | `0` |

For all temporal records, V116 trace query avg was `4929.982` and V125 temporal route-all query avg was `5395.908`. V125 remains below the normal `6K` temporal subset average, but there are local long-output risks: V125 has `2` temporal records over `8K` query tokens, with max `21404`.

## Gain patterns

### Local context supplies a missing time anchor

V125 often fixes cases where V116 selected the event row but answered the mention date, a neighboring unrelated date, or an insufficient answer.

| record | question | V116 | V125 | note |
|---|---|---|---|---|
| `77c7c748922005d1ca6e8229` | When did Gina get accepted for the design internship? | `2023-05-10` | `2023-05-27` | Neighbor text exposes the acceptance event around the selected internship turn. |
| `de49850323fff9e30e3f85a6` | When did John have a party with veterans? | `2023-05-20` | `2023-05-19` | The local window helps resolve "Friday before 20 May" rather than the conversation date. |
| `9633f51fac4067266e00aa7e` | When did John participate in a 5K charity run? | `2023-08-09` | `approximately August 5-6, 2023` | The added window exposes "last weekend" relative to the August 9 mention. |
| `507a52cbe63da61337791db9` | When is Joanna going to make Nate's ice cream for her family? | `2022-06-17` | `June 25-26, 2022` | The local window recovers the right "this weekend" anchor. |

### Local context turns insufficient answers into source-backed period answers

V125 also helps when V116 refuses despite enough temporal context being available nearby.

| record | question | V116 | V125 | note |
|---|---|---|---|---|
| `e1684220d528011b42524be4` | When did Deborah's mother pass away? | insufficient | "a few years ago" relative to January 2023 | Better preserves coarse temporal granularity. |
| `e839f93db9369bee676ce3c9` | When did Evan go skiing in Banff? | insufficient | `July 2023` | Nearby temporal context supports the month answer. |
| `566ed0b14fdda9f54bc9262c` | When will Evan and his partner have their honeymoon in Canada? | `2023-12-19 to 2023-12-25` | `February 2024` | Local context helps avoid overusing the mention-time week. |
| `1fa437f134b2779b077bb8c6` | When did Dave sell the car he restored last year? | insufficient | `2022` | Coarse answer is acceptable when the source only supports coarse granularity. |

## Loss patterns

### Local context can increase false insufficiency

The local window sometimes makes the reader stricter about whether a single selected turn explicitly states the answer, even when broader retrieved evidence supports it.

| record | question | V116 | V125 | risk |
|---|---|---|---|---|
| `a9b26389e6675bf930f8698f` | Which country was Jolene located in during the last week of August 2023? | `Brazil` | insufficient | The local window includes Rio de Janeiro evidence but the reader rejects country inference as not explicit. |
| `8136581d7bea1c09edbcc155` | When did Deborah go to an art show with Anna? | `2023-04-09` | insufficient | Added context appears to increase uncertainty instead of preserving the explicit date. |
| `21f5a526bb7978490a1feb58` | Which year did Evan start taking care of his health seriously? | `2021` | insufficient | V125 over-focuses on local health discussion and fails to carry through the year inference. |

### Local context can over-shift relative time

The added same-session context can push the model toward a nearby weekend or interval even when the base row already supported a simpler date.

| record | question | V116 | V125 | risk |
|---|---|---|---|---|
| `16d70285e40a99b09091bd7a` | How many weeks passed between Maria adopting Coco and Shadow? | `Approximately 2 weeks` | `1 week` | Duration arithmetic regresses after adding neighboring adoption context. |
| `6a4b3513a2918f903e26cbd8` | After how many weeks did Tim reconnect with the fellow Harry Potter fan from California? | `3 weeks` | `4 weeks` | Another duration arithmetic loss. |
| `acae332af0e2a71091b4c697` | When did Nate take time off to chill with his pets? | `2022-08-22` | `2022-08-27 to 2022-08-28` | "This weekend" was shifted to the later weekend rather than preserving the source date/week. |
| `11a386f7fad013ec77923fdd` | When is Nate hosting a gaming party? | `2022-06-11 to 2022-06-12` | `Two weekends after June 3, 2022 (approximately June 11-12, 2022)` | The answer contains the right span but a contradictory phrase, causing both judges to mark wrong. |

### Degenerate or overlong reasoning remains a risk

Two V125 temporal records exceed `8K` query tokens. The worst loss is `21f5a526bb7978490a1feb58` with `21404` query tokens and a final insufficient answer. Another loss, `6a00dae1ee0cf6a0b4b91a43`, ends with the degenerate answer `the date` despite identifying `2023-10-19` as a possible event time in the reasoning.

These failures are not caused by changed row ids. They are reader behavior triggered by a longer local context block and should be addressed by tighter evidence-unit selection or answer-format consistency, not by adding more rows.

## Decision

Keep V125 as a promising diagnostic candidate, not LTS.

The gain pattern is real and general: local source-backed context helps temporal questions resolve anaphora, relative dates, and event-vs-mention-time ambiguity. The loss pattern is also real: a fixed four-row temporal local context can make the reader over-infer weekends/durations, over-refuse when an answer requires light inference, or produce contradictory natural-language wrappers.

## Next method direction

Do not broaden local context. The next candidate should narrow or score temporal local context before materialization:

- Add a self-containedness gate: do not wrap a row that already contains a clear absolute date or complete event answer unless the row contains unresolved deixis/anaphora.
- Add evidence-density scoring for temporal local context: prefer neighbors that add explicit time anchors, entity resolution, or antecedents; skip neighbors that only add generic sentiment or unrelated session chatter.
- Keep raw row ids unchanged and source-backed. The local evidence unit should remain a compiler/text transformation, not a retrieval expansion.
- Add an answer consistency constraint that prefers a concise date/span when the reasoning contains one, and avoids contradictory wrappers such as "two weekends after" plus a one-weekend date span.
- Before LTS promotion, run LongMemEval answer/finalizer compatibility or a clean formal full run, because LME compiler compatibility alone does not prove the V121 source-grounded finalizer change.
