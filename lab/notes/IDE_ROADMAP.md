# QMPT Lab IDE – Roadmap

Goal: evolve the IDE into a full laboratory for QMPT simulations, pattern synthesis, and heavy compute usage.

## Near-term (v0.1.x → v0.2)
- Simulation launcher:
  - load scenario configs from `config/`,
  - pick seed/runtime/device (CPU/GPU),
  - stream stdout/stderr to a log pane.
- Formula-aware preview:
  - render LaTeX in viewer/notes using markdown + math.
- Run queue + status:
  - queued/running/finished/failed states,
  - quick links to logs in `lab/logs/`.
- Note templates:
  - experiment template pre-filled with scenario, seed, metrics checklist.

## Mid-term (v0.2 → v0.3)
- Pattern simulation hooks:
  - call future `qmpt.simulation` modules (population, anomaly injection, transfer cycle).
  - visualize trajectories \(\sigma_k(t), \mathcal{P}_k(t), A(\Psi), R_{\text{norm}}(\Psi)\).
- GPU/mainframe dispatch:
  - configurable backend (local CUDA vs remote cluster endpoint),
  - resource caps + telemetry.
- Result bundling:
  - tar/zip artifacts (configs, logs, plots) into `lab/logs/`.

## Long-term (v0.3+)
- Interactive pattern builder:
  - parameterize \(\Psi\), substrate \(\mathcal{S}\), transfer operators.
  - run “pattern synthesis” simulations and compare distances \(D(\Psi_1,\Psi_2)\).
- Collaborative mode:
  - shared notes/logs with conflict-free sync,
  - machine-readable run manifests.
- Rich visualization:
  - math-aware plots,
  - layer state dashboards,
  - replayable simulation timelines.
