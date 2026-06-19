# stage1_compact_selected_context_format_v215 rejection summary

## Decision

V215 is rejected and not promoted to LTS.

V215 changed only selected-context context organization: same-session materialized rows were rendered with a compact source-preserving wrapper. The goal was to reduce #2 query-token/context overhead without deleting raw evidence.

## Probe

Scope: LoCoMo non-adversarial probe200, diagnostic, config `configs/stage1_compact_selected_context_format_v215_seeded_qwen36_no_think_build4k_cached.json`.

Compared against the first 200 records of v214 LoCoMo full:

| Metric | Result |
|---|---:|
| answer diff | `86/200` |
| prompt diff | `198/200` |
| evidence row ids diff | `47/200` |
| evidence rows text diff | `198/200` |
| retrieval hits diff | `0/200` |
| selected-context trace diff | `200/200` |
| v214 first-200 avg query tokens | `6142.005` |
| v215 probe200 avg query tokens | `6017.23` |
| avg query token delta | `-124.775` |
| avg build tokens | `43657.36` both |

Run metrics:

- selected-context applied `198/200`; avg materialized rows `5.26`.
- answer cache hits/misses/writes `2/198/198`.
- repair triggered/applied `3/1`; repair query tokens `16621`.
- selected-context risk audit risk rows `708` on the probe.

## Diagnosis

The compact wrapper is clean, source-backed, and label-free, but it is not behavior-stable. It changes the prompt for nearly every selected-context sample, changes final evidence row inclusion on `47/200` samples through downstream prompt-budget effects, and causes `86/200` answer changes for only about `125` query tokens saved per sample on this probe.

This is too much reader drift for a formatting-only optimization. No full run or judge is needed because the probe already violates the stability requirement for a token-cost cleanup.

## Next

- Do not promote v215.
- Do not use pure wrapper compaction as the next #2 direction.
- If selected-context tokens are revisited, preserve the effective final evidence row sequence first, then test whether the reader remains answer-stable before running judge.
- Prefer source/span-preserving context organization or guarded rerank that reduces noise before prompt assembly without changing evidence semantics.

## Artifacts

- Probe experiment: `experiments/diagnostic/stage1_compact_selected_context_format_v215_locomo_probe200/`
- Probe outputs: `outputs/diagnostic/stage1_compact_selected_context_format_v215_locomo_probe200/`
- Method commit: `e54f6acba132d0b7671af08cce1fc8f49f721baa`
- Probe record commit: `da7a91a`
