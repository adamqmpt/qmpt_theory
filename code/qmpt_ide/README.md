# QMPT Lab IDE (v0.9.0 “Quantum Patterns & Examples”)

Dark-theme Tkinter IDE for QMPT experiments. Modular layout:

- `app.py` – entry point, wires everything.
- `core_config.py` – IDE config loader/saver.
- `core_runs.py` – run registry (JSONL), run metadata.
- `sim_runner.py` – backend abstraction (classical, quantum local simulator, hybrid cycle) + ensembles, derived metrics.
- `state.py` – shared app state.
- `ui_main.py` – assembles panels.
- `ui_docs.py` – Markdown doc browser/viewer.
- `ui_notes.py` – note editor + preview.
- `ui_runs.py` – run controls, history, log viewer.
- `ui_plots.py` – optional matplotlib plots (degrades gracefully if missing).
- `ui_layer.py` – layer/pattern inspector for completed runs.
- `theme.py` – styles.
- `quantum/` – quantum backends (local simulator + dummy), encodings, scenarios.

## How to run (EN)

```bash
python3 -m code.qmpt_ide.app
```

## Launching an experiment

1) Classical config (example, already in `lab/configs/classical_layer_dynamics.json`):

```json
{
  "backend": "classical",
  "experiment_type": "layer_dynamics",
  "scenario": "baseline_layer",
  "seed": 123,
  "horizon": 50,
  "dt": 1.0,
  "logs_dir": "lab/logs",
  "results_dir": "lab/results"
}
```

2) Quantum config (example, `lab/configs/quantum_layer_stress_probe.json`):

```json
{
  "backend": "quantum",
  "experiment_type": "layer_dynamics_quantum",
  "scenario": "layer_stress_probe",
  "seed": 321,
  "horizon": 16,
  "dt": 1.0,
  "logs_dir": "lab/logs",
  "results_dir": "lab/results",
  "quantum": {
    "n_qubits": 3,
    "circuit_depth": 2,
    "shots": 512,
    "backend_name": "local_simulator",
    "noise_model": "ideal"
  }
}
```

3) Hybrid config (example, `lab/configs/hybrid_layer_cycle.json`):

```json
{
  "backend": "hybrid",
  "experiment_type": "hybrid_layer_cycle",
  "probe_interval": 4,
  "horizon": 16,
  "dt": 1.0,
  "quantum": { "n_qubits": 3, "circuit_depth": 2, "shots": 256 }
}
```

4) Ensemble (repeat) config (example, `lab/configs/classical_ensemble.json`):

```json
{
  "backend": "classical",
  "ensemble": { "enabled": true, "mode": "repeat", "n_runs": 3, "description": "small repeat" }
}
```

5) In the IDE:
   - Set the config path (e.g., `lab/configs/classical_layer_dynamics.json` or `lab/configs/quantum_layer_stress_probe.json`).
   - Choose backend (`classical`, `quantum`, `hybrid`).
   - (Optional) toggle **Ensemble mode** and set `n_runs` and dataset note.
   - Click **Run**. Logs → `lab/logs/<run>.log`, results → `lab/results/<run>/`.
   - History lists runs; log viewer shows log content.
   - Plot panel saves plots to `lab/results/<run>/plot.png` if matplotlib is available (auto-detects classical vs quantum metrics).
   - Layer inspector surfaces metrics and patterns (classical) or quantum observables (quantum).

## QMPT core integration

- Core package: `code/qmpt_core` (models, metrics, scenarios, IO).
- Classical backend runs scenarios (baseline, anomaly injection, self-aware anomaly) and computes toy QMPT metrics.
- Quantum backend maps layer stress/novelty/anomaly proxies to shallow qiskit circuits, measures observables (expectation values, entropy, anomaly proxy).
- Hybrid backend couples classical layer dynamics with periodic quantum probes feeding back into stress/novelty.
- Results under `lab/results/<run_id>/`:
  - `metrics.json` (summary + scenario/seed/backend),
  - `timeseries.npz`:
    - classical: `t, stress, protection, novelty`
    - quantum: `t, stress, novelty, expectation_mean, entropy, anomaly_proxy`
    - hybrid: combined classical + quantum-derived arrays
  - `patterns.json` (classical patterns/metrics),
  - optional `plot.png` (if matplotlib is present).
- Run logs: `lab/logs/<run_id>.log`; registry: `lab/runs.jsonl`.

### Ensembles & datasets

- Enable via config block:

```json
"ensemble": {
  "enabled": true,
  "mode": "repeat",
  "n_runs": 8,
  "description": "my sweep"
}
```

- Dataset layout: `lab/datasets/<dataset_id>/`
  - `dataset_manifest.json` (runs, paths, metadata)
  - `ensemble_metrics.json` (aggregated anomaly/stress metrics)
- Each run still produces normal `lab/results/<run_id>/…` artifacts and registry entries (with dataset_id).

### CLI runner

- Headless runs (single or ensemble):

```bash
python -m code.qmpt_runner --config lab/configs/classical_ensemble.json --ensemble-enabled
```

Outputs run/dataset summary and reuses the same logs/results layout as the IDE.

### Quantum patterns & examples

- New quantum scenarios: entangled anomaly pair, transfer chain, measurement-induced collapse (`lab/configs/quantum_*.json`).
- Quantum metrics: entanglement entropy, continuity/fidelity, collapse delta, plus derived expressions via `derived_metrics`.
- Expression layer: add arithmetic formulas over metrics; results stored under `derived` in metrics JSON.
- Quantum examples doc: `lab/quantum/README_QUANTUM_EXAMPLES_en.md`.

## Roadmap (summary)

- v0.9.0 (current): Quantum Patterns & Examples — quantum scenarios/metrics/derived expressions, quantum example browser, improved plotting.
- v0.10.x: richer quantum noise/models, calibration refinements.
- v1.0: stable API, external data integration, reproducibility/export focus.

## Notes / RU hooks

- Matplotlib is optional; plotting disabled if not installed.
- qiskit is optional; if absent, quantum runs degrade to a dummy backend with clear status.
- Seeds and backend info are logged for determinism; metrics saved under `lab/results/<run>/metrics.json`.
- Run registry: `lab/runs.jsonl`.
- RU: добавьте русские подписи/разделы при локализации (все строки сгруппированы, чтобы облегчить перевод).

## Кратко (RU)

- Запуск: `python3 -m code.qmpt_ide.app`
- Бэкенды: классический (QMPT-сценарии) / квантовый (локальный симулятор qiskit) / гибрид (заглушка).
- Результаты: `lab/logs/<run>.log`, `lab/results/<run>/metrics.json`, `lab/results/<run>/timeseries.npz`.
- Конфиги: примеры в `lab/configs/` (classical_layer_dynamics.json, quantum_layer_stress_probe.json).
