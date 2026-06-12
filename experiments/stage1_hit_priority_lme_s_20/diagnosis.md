# Diagnosis for stage1_hit_priority_lme_s_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 9.85
- avg_context_chars: 11188.6
- avg_query_tokens: 2833.6
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.05
- offline_f1: 0.3708747809451135
- offline_bleu_unigram: 0.258693757223169
- evidence_recall: 1.0

## Interpretation

- The adapter duplicate-source fix allowed the run to complete beyond sample 3.
- Evidence recall is saturated on the first 20 samples, so failures should be investigated via judge and answer normalization rather than retrieval expansion first.
- Judge dry-run is available, but real judge accuracy is blocked until the DeepSeek key is exported to the environment.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
