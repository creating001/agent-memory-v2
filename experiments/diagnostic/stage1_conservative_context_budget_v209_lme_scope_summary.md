# stage1_conservative_context_budget_v209 LME scope summary

## Decision

V209 is an LME-safe conservative #2 context-budget candidate on top of the v207 LTS.

It changes v207's trace-only `context_budget_audit` into an actual retrieval `context_budget` with a conservative `22000` source-character budget, `32` protected/minimum anchors, and `max_hits=60`. This is intentionally wider than rejected v208's `16000` budget because v208 caused one LME prompt/evidence-row drift.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or budget gates.
- The budget is route-general across `current_state`, `fact_lookup`, `list_count`, `profile_preference`, and `temporal_lookup`.

## Full LME Verification

| Check | Result |
|---|---:|
| v209 vs v207 answer diff | `0/500` |
| route diff | `0/500` |
| prompt diff | `0/500` |
| evidence rows diff | `0/500` |
| retrieval hits diff | `137/500` |
| pre-budget hits diff | `0/500` |
| effective selected-context diff | `0/500` |
| context-budget applied | `500/500` |
| drop samples / total dropped / avg dropped | `137 / 416 / 0.832` |
| context-budget audit prompt risk | `0` |
| context-budget audit selected-context risk | `0` |
| answer cache | `500/0/0` |
| inherited judge accuracy | strict/lenient `0.834000 / 0.846000` |

Token accounting is unchanged from v207 on LME: avg build tokens `85393.566`, avg query tokens `6580.196`.

## Interpretation

V209 fixes the main v208 issue on LME: actual retrieval tail trimming no longer changes prompt or evidence rows. It reduces #2 retrieval candidate noise in trace-visible retrieval hits, but it does not yet reduce final query tokens because the retained evidence rows and prompt are unchanged.

Do not promote before LoCoMo full verification.

## Artifacts

- Config: `configs/stage1_conservative_context_budget_v209_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `7d604fa0b83a1608fbf967053cfa96822b2db0e9`
- LME full: `experiments/diagnostic/stage1_conservative_context_budget_v209_lme_s_full/`
- Outputs: `outputs/diagnostic/stage1_conservative_context_budget_v209_lme_s_full/`
