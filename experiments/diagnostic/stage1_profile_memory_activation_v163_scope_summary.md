# stage1_profile_memory_activation_v163 diagnostic summary

## Purpose

V163 tests whether source-backed typed build memory can safely help `profile_preference` answers at query time.

The method inherits v162 LTS and adds a narrow Profile Memory Activation Guide only for `profile_preference` routes. The guide exposes up to four activated build-memory records, but only when each record links back to visible raw Memory Context rows. It is framed as a preference/profile index, not independent evidence.

This targets risk #5: build memory should support organization, lifecycle/state reasoning, and query-time activation rather than acting only as a retrieval index. The run also checks risk #1 because profile methods can easily drift into benchmark-shaped preference heuristics.

## Config

- Config: `configs/stage1_profile_memory_activation_v163_qwen36_no_think_build4k_cached.json`
- Parent LTS: `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json`
- Changed-answer scope: LongMemEval-S `profile_preference`
- Prediction run: `stage1_profile_memory_activation_v163_lme_profile_preference`
- Tests: `python -m unittest discover -s src/tests` passed before this summary, `242` tests.
- Prediction commit recorded by run: `4686804`
- Dirty state in run manifest: expected; v163 source/config files were uncommitted during prediction.

## Method

The implementation is intentionally narrow:

- Only `profile_preference` routes can enable the guide through route overrides.
- A memory record is eligible only if its source ids map to visible raw Memory Context rows.
- Preference/profile records get priority; event/fact/state records require question-term overlap.
- The prompt states that the guide is not independent evidence and final claims must still be verified against raw rows.
- No gold answers, judge outputs, benchmark labels, sample ids, row indices, test feedback, or sample-level rules are used.

## Metrics

LongMemEval-S profile-preference diagnostic prediction:

| Metric | Value |
|---|---:|
| Samples | `15` |
| Answer cache | `0` hits, `15` misses, `15` writes |
| avg build tokens | `88100.333` |
| avg query tokens | `5529.200` |
| avg compiled evidence items | `35.733` |
| avg compiled memory records | `2.933` |
| Profile guide prompts | `13/15` |

Changed answers vs v162: `9/15`.

Dual DeepSeek flash judge on the 9 changed answers:

| Version | strict | lenient |
|---|---:|---:|
| v162 parent answers | `3/9` = `0.333333` | `4/9` = `0.444444` |
| v163 answers | `2/9` = `0.222222` | `3/9` = `0.333333` |

Judge token usage:

| Version | prompt tokens | completion tokens | total tokens |
|---|---:|---:|---:|
| v162 parent answers | `3768` | `3673` | `7441` |
| v163 answers | `3616` | `3606` | `7222` |

## Diagnosis

V163 is clean but negative.

The main failure mode is over-abstention. The guide made the answer prompt more cautious on advice/profile questions where the user expected a compatible recommendation derived from durable interests or prior choices. The clearest regression is the cultural-events question: v162 used language-learning and cultural-exchange interests to suggest event types, while v163 answered that there was not enough information to recommend specific events.

This is not a leakage issue. The risk is methodological: putting profile activation text directly into the answer prompt can turn source-grounding into excessive specificity requirements. For profile/advice questions, the system often needs to separate two operations:

- source-backed activation of user preferences and constraints;
- general, clearly qualified suggestion generation that does not invent user facts.

V163 mixed those two operations inside the answer prompt and reduced accuracy.

## Decision

Do not promote v163 to LTS.

V162 remains the current local LTS. V163 reduces one narrow #5 implementation risk in form, but it worsens the main judge metric on changed LongMemEval profile answers, so it cannot replace v162.

## Next Step

Do not broaden profile memory guides. The next #5 attempt should use v162 lifecycle/activation signals in an answer-slot-aware way:

- activate source-backed preferences as constraints, not as a reason to require named entities;
- preserve compatible recommendation behavior when the user asks for advice;
- use typed memory for conflict/lifecycle organization before final answer, not as a broad extra prompt block;
- judge changed answers before running full or LoCoMo evaluations.

## Outputs

- LME profile predictions: `outputs/diagnostic/stage1_profile_memory_activation_v163_lme_profile_preference/predictions.jsonl`
- LME profile traces: `outputs/diagnostic/stage1_profile_memory_activation_v163_lme_profile_preference/traces.jsonl`
- Changed-answer files: `outputs/diagnostic/stage1_profile_memory_activation_v163_lme_changed_vs_v162/`
- Changed-answer judge metrics snapshot: `experiments/diagnostic/stage1_profile_memory_activation_v163_lme_changed_vs_v162/metrics.json`
- Run record: `experiments/diagnostic/stage1_profile_memory_activation_v163_lme_profile_preference/`

