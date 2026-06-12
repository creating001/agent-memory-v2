# Diagnosis for stage1_concise_lme_s_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 9.41
- avg_context_chars: 11406.68
- avg_query_tokens: 2880.17
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.
- answer_style: concise
- offline_exact: 0.4
- offline_f1: 0.5320425887579914
- offline_bleu_unigram: 0.4974012812169807
- evidence_recall: 0.95
- single_session_exact: 0.5571428571428572
- multi_session_exact: 0.03333333333333333

## Interpretation

- Concise prompting scales reasonably on single-session-user examples.
- Multi-session examples are the dominant weakness even when labeled answer-session recall is fairly high.
- The next clean method should improve multi-session context assembly, likely by increasing support coverage and requiring answer synthesis from multiple evidence rows.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
