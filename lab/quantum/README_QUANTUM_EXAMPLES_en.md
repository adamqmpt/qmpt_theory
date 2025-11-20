# QMPT Quantum Examples (v0.9.0)

Three small, inspectable quantum scenarios you can run via configs under `lab/configs/` (backend `quantum`):

## 1. Entangled anomaly pair (`quantum_entangled_anomaly.json`)

- Circuit (2–3 qubits):
  - Prepare |0 0 …>
  - Hadamard on q0
  - RY(theta) on q1 (anomaly qubit)
  - CNOT q0→q1 (and optional entangle q2)
- QMPT view: q1 models \(\Psi_{\text{anom}}\) coupled to a background pattern.
- Metrics:
  - `entanglement_entropy` (S(q0|rest))
  - `R_quantum` (entropy of full state)
  - `anomaly_visibility` (|<Z> on anomaly|)
- Derived example: `R_quantum_norm = R_quantum / (1 + stress)` (see config).

## 2. Quantum transfer chain (`quantum_transfer_chain.json`)

- Circuit (3–4 qubits):
  - Initialize |1 0 0 …>
  - SWAP-like moves along the chain + small RZ noise each step.
- QMPT view: transfer of a pattern across substrates \(\mathcal{S}_1 \to \mathcal{S}_2 \to …\).
- Metrics:
  - `fidelity` timeseries vs initial state
  - `entanglement` (entropy of q0 marginal)
  - `fidelity_final`, `fidelity_min`, continuity loss (`1 - fidelity_final` as derived).

## 3. Measurement-induced collapse (`quantum_measurement_collapse.json`)

- Circuit (2 qubits):
  - RY(theta) on q0
  - CNOT q0→q1
  - Interpret measurement as collapse via sampled counts.
- QMPT view: probing an anomaly superposition with a measurement probe.
- Metrics:
  - `pre_entropy` (von Neumann of statevector)
  - `post_entropy` (from measurement distribution)
  - Derived: `collapse_delta = pre_entropy - post_entropy`.

## How to run

GUI: set config path to one of the above, choose backend `quantum`, run.  
CLI: `python -m code.qmpt_runner --config lab/configs/quantum_entangled_anomaly.json`

If qiskit is missing, runs degrade gracefully with `backend=quantum_dummy`.
