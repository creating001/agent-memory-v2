# Experiments

This directory is the human-readable entry point for formal and diagnostic runs.

Each run directory should include:

- `summary.md`: purpose, scope, config, git commit or no-git status, metrics, token cost, and output paths.
- `metrics.json`: machine-readable metrics, including token cost.
- `diagnosis.md`: short interpretation, failure modes, and next steps.
- `manifest.json`: run metadata, clean assertions, git state, and artifact paths.
- `config_snapshot.json`: exact config used by the run.

Formal benchmark runs must record local git commit and dirty state. If the workspace is not a git repository or has uncommitted changes, the summary must say so explicitly.

Offline judge outputs may be stored in the corresponding run directory, but they must never be consumed by prediction, retrieval, compiler, answer, or verifier code.
