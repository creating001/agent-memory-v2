# Diagnosis for stage1_qwen30b_lme_s_3

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 3
- avg_compiled_evidence_items: 10.0
- avg_context_chars: 10923.0
- avg_query_tokens: 2798.6666666666665
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.11111111111111112
- offline_bleu_unigram: 0.06666666666666667
- evidence_recall: 0.3333333333333333

## Interpretation

- Current retrieval is usable enough to validate traceability but too weak for quality claims.
- The next clean ablation should target retrieval recall and compiler selection while keeping raw evidence source links intact.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
