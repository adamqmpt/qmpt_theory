# QMPT Lab IDE Roadmap

- **v0.4.x (current)**
  - Modular UI (docs, notes, runs, plots).
  - Classical simulation pipeline (toy layer dynamics): logs + results + metrics.
  - Run registry (JSONL), log viewer, optional matplotlib plots.
  - Backend abstraction (classical + quantum stub).

- **v0.5**
  - Implement real QMPT metrics \(A(\Psi), R_\text{norm}(\Psi), \mathcal{O}_\text{self}(\Psi)\) in classical backend.
  - UI for inspecting pattern-level metrics and layer trajectories \(\mathcal{S}_k(t)\).
  - Export results to CSV/JSON from UI.

- **v0.6**
  - Quantum backend integration (Qiskit/Cirq or similar).
  - Presets comparing classical vs quantum toy experiments.
  - Basic resource/telemetry display for backends (CPU/GPU/qubits).

- **v1.0**
  - Stable API between IDE and backends.
  - Documented workflows (theory → config → run → metrics → interpretation).
  - Improved error handling, tests, localization (EN/RU), and packaging.
