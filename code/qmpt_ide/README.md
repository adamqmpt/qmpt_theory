# QMPT Lab IDE (v0.4.0)

Dark-theme Tkinter IDE for QMPT experiments. Architecture is modular:

- `app.py` – entry point, wires everything.
- `core_config.py` – IDE config loader/saver.
- `core_runs.py` – run registry (JSONL), run metadata.
- `sim_runner.py` – backend abstraction (classical implemented, quantum stub).
- `state.py` – shared app state.
- `ui_main.py` – assembles panels.
- `ui_docs.py` – Markdown doc browser/viewer.
- `ui_notes.py` – note editor + preview.
- `ui_runs.py` – run controls, history, log viewer.
- `ui_plots.py` – optional matplotlib plots (degrades gracefully if missing).
- `theme.py` – styles.

## How to run

```bash
python3 -m code.qmpt_ide.app
```

## Running an experiment

1. Prepare a config JSON under `lab/configs/` (example):

```json
{
  "backend": "classical",
  "experiment_type": "layer_dynamics",
  "seed": 123,
  "horizon": 100,
  "dt": 1.0,
  "logs_dir": "lab/logs",
  "results_dir": "lab/results"
}
```

2. In the IDE:
   - Set the config path (e.g. `lab/configs/example.json`).
   - Choose backend (`classical` or `quantum` stub).
   - Click Run. Logs go to `lab/logs/<run>.log`, results to `lab/results/<run>/`.
   - History lists runs; log viewer shows log content.
   - Plot panel saves plots to `lab/results/<run>/plot.png` if matplotlib is available.

## Roadmap (summary)

- v0.4.x: modular UI, classical pipeline (toy layer dynamics), run registry, plotting.
- v0.5: real QMPT metrics \(A(\Psi), R_\text{norm}(\Psi), \mathcal{O}_\text{self}(\Psi)\); richer config schema; CLI helpers.
- v0.6: quantum backend integration (Qiskit/Cirq stub → real), config presets for classical vs quantum.
- v1.0: stable API between IDE and backends, end-to-end examples, localization (EN/RU) for UI strings.

## Notes

- Matplotlib is optional; plotting is disabled if not installed.
- All seeds and backend info are logged for determinism; metrics saved under `lab/results/<run>/metrics.json`.
- Run registry: `lab/runs.jsonl`.
