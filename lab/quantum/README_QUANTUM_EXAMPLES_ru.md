# Примеры квантовых сценариев QMPT (v0.9.0)

Три небольших сценария (backend `quantum`), конфиги в `lab/configs/`:

## 1. Пара «аномалия–фон» (`quantum_entangled_anomaly.json`)

- Схема (2–3 кубита):
  - |0 0 …>
  - H на q0
  - RY(theta) на q1 (анomaly)
  - CNOT q0→q1 (опция: запутать q2)
- Метрики: энтропия запутанности, `R_quantum`, видимость аномалии.
- Пример derived: `R_quantum_norm = R_quantum / (1 + 0.1)`.

## 2. Цепочка переноса (`quantum_transfer_chain.json`)

- Схема: SWAP-перемещения состояния |1> вдоль цепочки + слабый шум RZ.
- Метрики: fidelity (время), `entanglement`, `fidelity_final/min`, continuity loss.

## 3. Коллапс при измерении (`quantum_measurement_collapse.json`)

- Схема: RY(theta) на q0, CNOT q0→q1, далее измерение как коллапс.
- Метрики: `pre_entropy` (фон Неймана) vs `post_entropy` (из распределения измерений), `collapse_delta`.

## Запуск

GUI: выбрать конфиг, backend `quantum`, нажать Run.  
CLI: `python -m code.qmpt_runner --config lab/configs/quantum_entangled_anomaly.json`

При отсутствии qiskit сценарии переходят в режим `quantum_dummy` (без аварии).
