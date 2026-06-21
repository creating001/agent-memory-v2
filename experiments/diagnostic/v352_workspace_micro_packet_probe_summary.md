# v352 workspace micro packet probe summary

## Purpose

v352 keeps v351's build-owned `memory_workspace_policy` adapter and `inline_spaced` raw Memory Context, then changes only the source-backed Working Memory Packet presentation used when the policy safely replaces legacy current/fact/profile guides.

The goal is to reduce query prompt boilerplate without removing raw evidence rows, and to make the query-level workspace activation visible to the Context Manifest and answer verifier.

## Clean boundary

Prediction uses no gold answers, judge outputs, benchmark tags, sample ids, test feedback, or sample-level rules. Derived memory remains activation/index only; final facts must still be grounded in raw Memory rows. The DeepSeek judge was not run in this turn because `DEEPSEEK_API_KEY` was not present in the shell, and `.env` was not read.

## Changes

- Added `working_memory_packet_format="micro"` while preserving `slot`, `type`, `focus`, `hint`, and `src=Memory N`.
- Added compiler diagnostics for selected workspace packet source labels, slots, focus counts, and verifier checks.
- Added `context_manifest.context_organization.workspace_query_policy`.
- Added answer-verifier trace fields for query-level workspace policy activation.
- Added runner metric aggregation for workspace query policy verifier fields.

## Runs

| Run | Path |
|---|---|
| LME compile scan | `outputs/diagnostic/v352_workspace_micro_packet_compile_scan_lme_probe50/traces.jsonl` |
| LoCoMo compile scan | `outputs/diagnostic/v352_workspace_micro_packet_compile_scan_locomo_probe50/traces.jsonl` |
| LME answer probe | `outputs/diagnostic/v352_workspace_micro_packet_lme_probe50/predictions.jsonl` |
| LoCoMo answer probe | `outputs/diagnostic/v352_workspace_micro_packet_locomo_probe50/predictions.jsonl` |
| Prompt-effect files | `outputs/diagnostic/v352_vs_v350_lme_probe50_prompt_effect/`, `outputs/diagnostic/v352_vs_v350_locomo_probe50_prompt_effect/` |

## Compile diff vs v351

| Benchmark | n | row set diff | row order diff | prompt diff | avg prompt char delta | workspace policy applied |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | 50 | 0 | 0 | 33 | `-50.56` | 33 |
| LoCoMo non-adversarial probe50 | 50 | 0 | 0 | 18 | `-29.26` | 18 |

Not-applied reason was unchanged: LME `route_not_enabled=17`, LoCoMo `route_not_enabled=32`.

## Query token findings

Raw answer-probe totals include fresh generation noise. The prompt-token comparison is the cleanest query-input signal:

| Benchmark | v350 avg prompt tokens | v352 avg prompt tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S probe50 | `4968.52` | `4956.02` | `-12.50` |
| LoCoMo non-adversarial probe50 | `4879.86` | `4870.94` | `-8.92` |

Fresh total query tokens were LME `5202.84 -> 5194.52` and LoCoMo `5331.48 -> 5358.64`; the LoCoMo increase came from longer completions, not prompt growth. Under prompt-effect/cache-aligned accounting that reuses v350 answers for unchanged prompts:

| Benchmark | prompt-changed | answer-changed on prompt-changed | adjusted avg total query tokens |
|---|---:|---:|---:|
| LongMemEval-S probe50 | 33 | 0 | `5188.24` |
| LoCoMo non-adversarial probe50 | 18 | 15 | `5328.10` |

## Decision

Keep v352 as a clean query-token/system-observability candidate, not LTS. It reduces prompt tokens and improves query-level workspace/verifier traceability, but LoCoMo has 15 prompt-effect answer changes and still needs changed-answer dual DeepSeek judge before any LTS decision.

## Next

- Run LoCoMo prompt-effect changed-answer judge for `outputs/diagnostic/v352_vs_v350_locomo_probe50_prompt_effect/answer_changed_on_prompt_changed/` once `DEEPSEEK_API_KEY` is available in the environment.
- If judge is neutral or positive, test a larger/full cache-aligned diff.
- If judge regresses, keep the Context Manifest/verifier diagnostics and revisit packet wording or cache seeding before changing prompt surface.
