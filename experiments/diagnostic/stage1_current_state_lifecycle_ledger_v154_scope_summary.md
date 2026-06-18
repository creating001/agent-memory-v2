# V154 Current-State Lifecycle Ledger

## Decision

Promote `configs/stage1_current_state_lifecycle_ledger_v154_qwen36_no_think_build4k_cached.json` to local LTS.

V154 inherits v151 and adds a Current-State Lifecycle Ledger only inside the narrow `current_state` repair pass. The ledger is a compact source index over the same raw Memory Context rows. It is not exposed as standalone reader evidence, does not expose typed memory text, and does not broaden the primary answer prompt or repair trigger set.

## Metrics

| Benchmark | Result |
|---|---:|
| LongMemEval-S full | strict/lenient `411/500` / `417/500` = `0.822000 / 0.834000` |
| LoCoMo non-adversarial full | strict/lenient `1216/1540` / `1256/1540` = `0.789610 / 0.815584` |

LongMemEval is paired-delta derived from v151: v154 r3 changed `1/500` answer. The changed-answer paired dual judge was `1/1` strict and `1/1` lenient for both v151 and v154, so full accuracy is unchanged. LoCoMo changed `0/1540` answers versus v151.

## Runs

Final diagnostic prediction runs:
- `outputs/diagnostic/stage1_current_state_lifecycle_ledger_v154_lme_s_full_r3/`
- `outputs/diagnostic/stage1_current_state_lifecycle_ledger_v154_locomo_nonadv_full_r3/`

Changed-answer judge:
- `outputs/diagnostic/stage1_current_state_lifecycle_ledger_v154_lme_changed_vs_v151/v151_dual_judge.json`
- `outputs/diagnostic/stage1_current_state_lifecycle_ledger_v154_lme_changed_vs_v151/v154_dual_judge.json`

Human-readable run records:
- `experiments/diagnostic/stage1_current_state_lifecycle_ledger_v154_lme_s_full_r3/`
- `experiments/diagnostic/stage1_current_state_lifecycle_ledger_v154_locomo_nonadv_full_r3/`

Token cost from r3:
- LongMemEval avg build/query visible tokens: `85393.566 / 6179.012`
- LoCoMo avg build/query visible tokens: `62015.574 / 6047.909`

## Diagnosis

External methods used as design input:
- Graphiti/Zep: episode/raw backpointers plus temporal lifecycle/invalidation should guide update reasoning without deleting old evidence.
- Mem0/MemOS/OpenMemory: lifecycle operations should be auditable and non-destructive.
- Hindsight: separate raw/stated facts from inferred or summarized memory; use derived memory as activation/index, not as final evidence.

The first v154 diagnostic made ledger candidate selection too broad. Generic terms such as `been`, `working`, and `current` pulled unrelated rows into the ledger and made the repair model over-conservative on a current-role duration question. The final r3 version filters those generic terms; if a current-state question has no concrete source-backed slot terms, no ledger is emitted and v151 behavior is preserved.

## Risk Conclusion

Compared with v151:
- #4 verifier overreach risk is not increased: trigger set remains `current_state` uncertain/modal repair only.
- #5 lifecycle/update reasoning risk is lower: repair now has a configurable, source-backed lifecycle index when concrete slot evidence exists.
- Accuracy is unchanged on both benchmark scopes.

Remaining risks:
- #1 granularity/profile and #3 selected-context generality are still unresolved.
- #2 top-k/context noise still needs coverage-preserving organization rather than pruning.
- #5 still needs broader lifecycle/conflict/update management beyond the narrow current-state repair pass.

## Clean Note

Prediction code uses only question, route, draft answer JSON, raw Memory Context, and prediction-time traces. No gold answers, judge outputs, benchmark labels, sample ids, row indices, or test feedback are used by prediction, retrieval, compiler, repair, or cache construction.

Promotion commit: this file is committed together with `eval: promote v154 lifecycle ledger lts`; use `git log --oneline -- experiments/diagnostic/stage1_current_state_lifecycle_ledger_v154_scope_summary.md` for the exact local commit.
