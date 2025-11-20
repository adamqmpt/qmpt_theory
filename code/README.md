# Code overview / Краткое описание кода

This directory contains executable tooling for QMPT:

- `qmpt_ide/` — QMPT Lab IDE (Tkinter, dark theme), version 0.9.0 “Quantum Patterns & Examples”.
- `qmpt_core/` — minimal QMPT models/metrics/scenarios shared by the IDE.

## QMPT Lab IDE (EN)

- Backends: classical (QMPT scenarios), quantum (qiskit local simulator), hybrid (classical+quantum probe).
- Quantum examples: entangled anomaly pair, transfer chain, measurement collapse (`lab/configs/quantum_*.json`, docs in `lab/quantum/README_QUANTUM_EXAMPLES_en.md`).
- Expression layer: `derived_metrics` formulas over metrics; stored under `derived` in metrics JSON.
- Ensembles: repeat/sweep runs with dataset manifests under `lab/datasets/`, aggregate metrics.
- CLI: headless runner `python -m code.qmpt_runner --config ...` (list quantum examples with `--examples quantum`).
- Run entry point (GUI): `python3 -m code.qmpt_ide.app`
- Results: `lab/logs/<run>.log`, `lab/results/<run>/metrics.json`, `lab/results/<run>/timeseries.npz`
- Config samples: `lab/configs/classical_layer_dynamics.json`, `lab/configs/quantum_layer_stress_probe.json`, `lab/configs/quantum_entangled_anomaly.json`, `lab/configs/hybrid_layer_cycle.json`, `lab/configs/classical_ensemble.json`
- Optional deps: matplotlib (plots), qiskit (quantum backend)

## QMPT Lab IDE (RU)

- Бэкенды: классический (QMPT-сценарии), квантовый (локальный симулятор qiskit), гибрид (классика + квантовый зонд).
- Ансамбли: повторы/свипы, датасеты в `lab/datasets/`, агрегированные метрики.
- CLI: `python -m code.qmpt_runner --config ...`
- Запуск GUI: `python3 -m code.qmpt_ide.app`
- Результаты: `lab/logs/<run>.log`, `lab/results/<run>/metrics.json`, `lab/results/<run>/timeseries.npz`
- Примеры конфигов: `lab/configs/classical_layer_dynamics.json`, `lab/configs/quantum_layer_stress_probe.json`, `lab/configs/hybrid_layer_cycle.json`, `lab/configs/classical_ensemble.json`
- Необязательные зависимости: matplotlib (графики), qiskit (квантовый бэкенд)
