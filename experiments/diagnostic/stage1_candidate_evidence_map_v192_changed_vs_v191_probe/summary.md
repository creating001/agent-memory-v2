# stage1_candidate_evidence_map_v192 changed-answer judge

V192 is rejected. On the two activation-probe rows where v192 changed v191, dual `deepseek-v4-flash` judge drops from v191 `2/2` strict and lenient to v192 `1/2`.

The negative row is `acae332af0e2a71091b4c697`: v191 answers `2022-08-22` and both judge runs mark it correct; v192 answers `The weekend of August 27-28, 2022` and both judge runs mark it wrong.

Artifacts are under `outputs/diagnostic/stage1_candidate_evidence_map_v192_changed_vs_v191_probe/`.
