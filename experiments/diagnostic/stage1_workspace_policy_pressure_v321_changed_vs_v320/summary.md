# v321 changed-answer judge vs v320

Purpose: evaluate only the answer changes caused by v321 workspace policy + compact selected context + context-pressure compiler. This is offline evaluation only; it is not used by prediction logic.

## Scope

| subset | changed answers | prompt diff | evidence source-order diff |
| --- | ---: | ---: | ---: |
| LME smoke5 | 0/5 | 0/5 | 0/5 |
| LoCoMo smoke5 | 2/5 | 5/5 | 0/5 |
| LME op21 | 3/21 | 7/21 | 7/21 |

## Dual judge result

| subset | old v320 strict/lenient | new v321 strict/lenient | transition |
| --- | ---: | ---: | --- |
| LoCoMo changed 2 | 2/2 / 2/2 | 2/2 / 2/2 | no regression |
| LME op changed 3 | 2/3 / 2/3 | 2/3 / 2/3 | no regression |

Changed answer notes:

- `0ef0216553b4eeff9be57e45`: old and new both correct.
- `628d9b1436fa405b91ee2820`: old and new both correct.
- `8ff24d864a7513f4c6eb5f33`: capitalization-only answer change, both correct.
- `d4bfe0f95ae6b5d7a565a8c1`: capitalization-only answer change, both correct.
- `ea4e66b0d90b6834b4168cfe`: old refusal and new `email inbox` are both wrong.

Judge paths:

- `locomo_smoke5/old_v320_dual_judge.json`
- `locomo_smoke5/new_v321_dual_judge.json`
- `lme_op21/old_v320_dual_judge.json`
- `lme_op21/new_v321_dual_judge.json`

Clean note: labels and judge outputs are read only after prediction; no gold answer, judge output, benchmark label, sample id, or test feedback is used by retrieval, compiler, answer, verifier, cache construction, or memory build.
