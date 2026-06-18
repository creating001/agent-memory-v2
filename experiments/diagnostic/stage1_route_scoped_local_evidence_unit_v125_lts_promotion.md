# V125 LTS promotion

## Decision

Promote `configs/stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json` to the current local LTS.

This promotion follows the updated local LTS rule: a new LTS may replace the previous LTS when it clearly reduces one or more of the five goal risks. Performance improvement is a strong additional signal, but not the only promotion condition. When predictions change, dual `deepseek-v4-flash` judge remains the primary performance evidence.

## Previous LTS

- Config: `configs/stage1_extended_selected_context_v116_qwen36_no_think_build4k_cached.json`
- LongMemEval-S full strict/lenient: `0.812000 / 0.834000`
- LoCoMo non-adversarial full strict/lenient: `0.779221 / 0.807143`

## V125 method

V125 inherits V121/V116 and changes only one retrieval-context behavior:

- build memory, raw retrieval top-k, granularity profiles, compiler, answer prompt, and fact/list/profile selected-context behavior stay aligned with V116/V121
- finalizer uses V121 `source_grounded_consistency_guard`, reducing broad mechanical finalizer risk
- `temporal_lookup` route may materialize a small same-session local evidence unit around up to four short anaphoric center rows
- prediction uses only question text, raw Memory Context, same-session visible turn order, and prediction-time route

No gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level shortcuts enter prediction.

## Evidence

### Five Goal Risk Audit

| goal risk | V116 status | V125 delta | LTS decision |
|---|---|---|---|
| #1 Granularity / profile design-for-benchmark | Still depends on the existing granularity/profile design. | No material change. | Not solved; keep as priority risk. |
| #2 Multi-route top-k / context noise / rerank | Retrieval top-k and route fan-out remain broad. | No material change. | Not solved; keep rerank/evidence-budget candidates active. |
| #3 Selected context long/short-turn heuristic | V116 selected context is still tied to the existing short-turn policy. | Partially reduced: V125 scopes local context to prediction-time `temporal_lookup` instead of broadening the long/short-turn rule globally. LoCoMo non-temporal prompts and all evidence row ids are unchanged; LME prompts/rows are unchanged. | Accept partial risk reduction, but keep V135 narrower temporal gating as the next step because badcases remain. |
| #4 Mechanical finalizer | V116 LTS uses `structured_evidence_mechanical`, which carried broad count/date/money/relative-time mechanical rules. | Reduced: V125 inherits V121 `source_grounded_consistency_guard`, which only expands refusal from source-grounded missing-detail evidence and does not compute answer patterns. | Solved enough for LTS replacement; continue forbidding sample-level rules. |
| #5 Build memory organization / update / conflict / query-time reasoning | Build memory is still mostly a retrieval aid. | No material change. | Not solved; keep V126/V127 and follow-up memory organization work active. |

### Supporting Risk Evidence

- Mechanical finalizer risk is reduced by inheriting V121 `source_grounded_consistency_guard`.
- V116 finalizer-impact audit found LME finalizer applied only `8/500` records and LoCoMo finalizer applied `0/1540`; the broad count/date/money/relative-time mechanical rules had no current LTS benefit evidence.
- V121 smoke on those LME finalizer-applied 8 records produced predictions identical to V116 while changing the trace reason to `source_grounded_missing_detail`.
- V125 narrows rejected V124 local evidence expansion from broad short-turn application to only `temporal_lookup`.
- V125 LoCoMo dry-run changed temporal prompts `338/338`, non-temporal prompts `0/1202`, and evidence row ids `0/1540`.
- V125 LME dry-run changed prompts `0/500`, evidence row ids `0/500`, routes `0/500`, and avg context delta `0.0`.

### Benchmark-Level Performance Evidence

| benchmark | V116 LTS | V125 evidence | delta / interpretation |
|---|---:|---:|---|
| LongMemEval-S full | strict/lenient `0.812000 / 0.834000` | inherited strict/lenient `0.812000 / 0.834000` | No new full answer/judge rerun. V125 has `0/500` prompt changes, `0/500` evidence-row changes, and V121 guard preserves outputs on the only 8 V116 finalizer-applied records. |
| LoCoMo non-adversarial full | strict/lenient `0.779221 / 0.807143` (`1200/1540`, `1243/1540`) | route-only merge strict/lenient `0.789610 / 0.807792` (`1216/1540`, `1244/1540`) | strict `+16/1540`; lenient `+1/1540`. Full route-only artifact, not a separate clean formal full rerun. |

The LoCoMo full route-only artifact is backed by `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/`.

### Route-Level Performance Detail

LoCoMo temporal paired dual judge:

| predictions | strict | lenient |
|---|---:|---:|
| V116 temporal subset | `0.772189` (`261/338`) | `0.786982` (`266/338`) |
| V125 temporal subset | `0.792899` (`268/338`) | `0.813609` (`275/338`) |
| paired gain/loss | `19/12`, net `+7` | `19/10`, net `+9` |

LoCoMo route-only isolated full artifact:

| predictions | strict | lenient |
|---|---:|---:|
| V116 current LTS full | `0.779221` (`1200/1540`) | `0.807143` (`1243/1540`) |
| V125 route-only merge | `0.789610` (`1216/1540`) | `0.807792` (`1244/1540`) |

LongMemEval:

- V125 compiler compatibility dry-run shows `0/500` prompt changes and `0/500` evidence-row changes relative to V116.
- V121 finalizer smoke shows the source-grounded guard preserves V116 outputs on the only 8 LME records where V116 finalizer applied.
- Therefore V125 is treated as inheriting V116 LME strict/lenient `0.812000 / 0.834000` for LTS bookkeeping, with explicit compatibility evidence rather than a new full LME answer rerun.

## Known Risks

V125 is not risk-free. Temporal badcase analysis found:

- gains mainly come from local time anchors, temporal anaphora, and event-vs-mention-time disambiguation
- losses include relative-time over-shift, false insufficiency, contradictory answer wrappers, and a small number of long-output outliers
- the worst V125 temporal query-token outlier is `21404`, so the next candidate should narrow local-context materialization

These risks do not erase the LTS promotion because V125 reduces goal risks #3 and #4 relative to V116 and has positive LoCoMo accuracy evidence. They do mean V125 is not the end state: goal risks #1, #2, and #5 remain open, and #3 is only partially reduced.

## Next Step

Start the next version from V125 LTS. The immediate follow-up candidate is a narrower temporal local-context policy with self-containedness / evidence-density gating, intended to preserve V125 gains while reducing temporal losses and long-output outliers.
