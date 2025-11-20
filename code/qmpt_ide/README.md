# QMPT Lab IDE (v0.6.0 “Quantum Bridge”)

Dark-theme Tkinter IDE for QMPT experiments. Modular layout:

- `app.py` – entry point, wires everything.
- `core_config.py` – IDE config loader/saver.
- `core_runs.py` – run registry (JSONL), run metadata.
- `sim_runner.py` – backend abstraction (classical, quantum local simulator, hybrid stub).
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

3) In the IDE:
- Set the config path (e.g., `lab/configs/classical_layer_dynamics.json` or `lab/configs/quantum_layer_stress_probe.json`).
- Choose backend (`classical`, `quantum`, `hybrid` stub).
- Click **Run**. Logs → `lab/logs/<run>.log`, results → `lab/results/<run>/`.
- History lists runs; log viewer shows log content.
- Plot panel saves plots to `lab/results/<run>/plot.png` if matplotlib is available (auto-detects classical vs quantum metrics).
- Layer inspector surfaces metrics and patterns (classical) or quantum observables (quantum).

## QMPT core integration

- Core package: `code/qmpt_core` (models, metrics, scenarios, IO).
- Classical backend runs scenarios (baseline, anomaly injection, self-aware anomaly) and computes toy QMPT metrics.
- Quantum backend maps layer stress/novelty/anomaly proxies to shallow qiskit circuits, measures observables (expectation values, entropy, anomaly proxy).
- Results under `lab/results/<run_id>/`:
  - `metrics.json` (summary + scenario/seed/backend),
  - `timeseries.npz`:
    - classical: `t, stress, protection, novelty`
    - quantum: `t, stress, novelty, expectation_mean, entropy, anomaly_proxy`
  - `patterns.json` (classical patterns/metrics),
  - optional `plot.png` (if matplotlib is present).
- Run logs: `lab/logs/<run_id>.log`; registry: `lab/runs.jsonl`.

## Roadmap (summary)

- v0.6.0 (current): Quantum Bridge — local simulator backend, QMPT→circuit encodings, quantum timeseries/metrics, UI backend selector.
- v0.7.x: hybrid classical–quantum loop, localization (EN/RU), backend plugins, richer viz.
- v0.8.x: optional remote/pluggable quantum backends, expanded scenarios.
- v1.0: stable API, full workflows, hardened tests/docs.

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
