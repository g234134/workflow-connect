# CI mirror: gov_core_system source (INT gate)

Portable **source-only** mirror for P6 INT nightly/PR workflows.

- **Why**: `01_Environments/python_venvs/gov_core_system` is a nested git worktree and is gitignored as a venv root; parent checkout cannot see `core/`.
- **What**: Wave 6/7/8 Tier-A modules + tests + minimal schemas needed by `_wave7_regression_gate.py`.
- **Not**: venv `Scripts`/`Lib`, secrets, runtime checkpoints (constitution §7 Z-VENV-TREE / Z-RUNTIME-CP).
- **CI**: workflows copy this tree onto the Master_Map cabin path before running the gate.

Do not treat this mirror as the DarkOps edit surface — edit the cabin, then refresh this mirror when landing CI assets.
