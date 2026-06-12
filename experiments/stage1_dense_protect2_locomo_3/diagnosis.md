# Diagnosis for stage1_dense_protect2_locomo_3

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 3
- avg_compiled_evidence_items: 20.0
- avg_context_chars: 5402.333333333333
- avg_query_tokens: 1654.6666666666667
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.09809523809523808
- offline_bleu_unigram: 0.05515151515151515
- evidence_recall: 1.0
- avg_embedding_tokens: 13490.0

## Interpretation

- Lexical protection fixes a visible dense-fusion temporal error while preserving dense recall gains.
- The next step should use a larger LoCoMo slice and judge accuracy to decide between equal RRF and protected fusion.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
