# Code overview / Краткое описание кода

This directory contains executable tooling for QMPT:

- `qmpt_ide/` — QMPT Lab IDE (Tkinter, dark theme), version 0.6.0 “Quantum Bridge”.
- `qmpt_core/` — minimal QMPT models/metrics/scenarios shared by the IDE.

## QMPT Lab IDE (EN)

- Backends: classical (QMPT scenarios), quantum (qiskit local simulator), hybrid (stub).
- Run entry point: `python3 -m code.qmpt_ide.app`
- Results: `lab/logs/<run>.log`, `lab/results/<run>/metrics.json`, `lab/results/<run>/timeseries.npz`
- Config samples: `lab/configs/classical_layer_dynamics.json`, `lab/configs/quantum_layer_stress_probe.json`
- Optional deps: matplotlib (plots), qiskit (quantum backend)

## QMPT Lab IDE (RU)

- Бэкенды: классический (QMPT-сценарии), квантовый (локальный симулятор qiskit), гибрид (заглушка).
- Запуск: `python3 -m code.qmpt_ide.app`
- Результаты: `lab/logs/<run>.log`, `lab/results/<run>/metrics.json`, `lab/results/<run>/timeseries.npz`
- Примеры конфигов: `lab/configs/classical_layer_dynamics.json`, `lab/configs/quantum_layer_stress_probe.json`
- Необязательные зависимости: matplotlib (графики), qiskit (квантовый бэкенд)
