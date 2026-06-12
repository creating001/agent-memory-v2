# Diagnosis for stage1_dense_protect2_lme_s_3

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 3
- avg_compiled_evidence_items: 9.666666666666666
- avg_context_chars: 11778.0
- avg_query_tokens: 2870.3333333333335
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.3844155844155845
- offline_bleu_unigram: 0.25
- evidence_recall: 1.0
- avg_embedding_tokens: 103881.66666666667

## Interpretation

- Lexical protection removes the observed LongMemEval regression from equal RRF.
- Dense still adds large embedding cost without quality gain on this slice, so full runs should either cache embeddings or gate dense use.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
