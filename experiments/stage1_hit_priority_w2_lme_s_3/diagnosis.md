# Diagnosis for stage1_hit_priority_w2_lme_s_3

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 3
- avg_compiled_evidence_items: 11.0
- avg_context_chars: 12947.0
- avg_query_tokens: 3240.6666666666665
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.3844155844155845
- offline_bleu_unigram: 0.25
- evidence_recall: 1.0

## Interpretation

- LongMemEval already has 3/3 evidence recall under hit-priority w1 for this diagnostic slice.
- Fixed w2 only raises token cost here, so it should not replace the w1 mainline without larger-slice evidence.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
