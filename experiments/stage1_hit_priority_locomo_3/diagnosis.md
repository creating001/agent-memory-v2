# Diagnosis for stage1_hit_priority_locomo_3

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 3
- avg_compiled_evidence_items: 20.0
- avg_context_chars: 5646.666666666667
- avg_query_tokens: 1731.3333333333333
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.07731481481481482
- offline_bleu_unigram: 0.0424192665571976
- evidence_recall: 0.3333333333333333

## Interpretation

- Hit-priority expansion fixes a compiler loss mode where direct BM25 hits were retrieved but excluded by chronological neighbor sorting.
- The remaining 2/3 LoCoMo misses are retrieval misses, not compiler drops, so the next clean step should add session-level or entity-aware retrieval views.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
