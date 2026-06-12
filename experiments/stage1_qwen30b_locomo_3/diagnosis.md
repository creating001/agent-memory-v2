# Diagnosis for stage1_qwen30b_locomo_3

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 3
- avg_compiled_evidence_items: 20.0
- avg_context_chars: 5871.666666666667
- avg_query_tokens: 1787.3333333333333
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.006472491909385113
- offline_bleu_unigram: 0.0033333333333333335
- evidence_recall: 0.0

## Interpretation

- LoCoMo needs a stronger first-stage retriever than turn-level BM25 on the question alone.
- The next clean ablation should add session/dialogue-level retrieval and fused source expansion without reading category or evidence labels during prediction.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
