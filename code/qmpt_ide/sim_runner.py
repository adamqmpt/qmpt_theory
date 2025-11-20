"""
Simulation runner abstraction with classical and quantum backends.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any

import numpy as np

from .state import repo_root


class BackendType(str, Enum):
    CLASSICAL = "classical"
    QUANTUM = "quantum"


@dataclass
class RunResult:
    run_id: str
    status: str
    metrics: Dict[str, float]
    log_path: Path
    results_path: Path
    backend: BackendType


class SimulationRunner:
    """
    Dispatches simulations based on backend. Classical is implemented;
    quantum is a stub for future integration.
    """

    def __init__(self, registry) -> None:
        self.registry = registry

    def run(self, config_path: Path, backend: BackendType) -> RunResult:
        cfg = self._load_experiment_config(config_path)
        run_id = self._generate_run_id(config_path, cfg)
        base_dir = repo_root()
        logs_dir = base_dir / cfg.get("logs_dir", "lab/logs")
        results_dir = base_dir / cfg.get("results_dir", "lab/results")
        logs_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"{run_id}.log"
        result_dir = results_dir / run_id
        result_dir.mkdir(parents=True, exist_ok=True)

        if backend == BackendType.CLASSICAL:
            return self._run_classical(cfg, run_id, log_path, result_dir)
        return self._run_quantum_stub(cfg, run_id, log_path, result_dir)

    def _load_experiment_config(self, path: Path) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _generate_run_id(self, config_path: Path, cfg: Dict[str, Any]) -> str:
        seed = cfg.get("seed", 42)
        backend = cfg.get("backend", "classical")
        payload = f"{config_path}-{seed}-{backend}-{time.time()}"
        return hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]

    def _run_classical(
        self,
        cfg: Dict[str, Any],
        run_id: str,
        log_path: Path,
        result_dir: Path,
    ) -> RunResult:
        seed = cfg.get("seed", 42)
        random.seed(seed)
        np.random.seed(seed)
        horizon = int(cfg.get("horizon", 100))
        dt = float(cfg.get("dt", 1.0))

        sigma = [float(cfg.get("sigma0", 0.2))]
        capacity = [float(cfg.get("capacity0", 1.0))]
        anomaly_idx = []

        with log_path.open("w", encoding="utf-8") as logf:
            logf.write(f"run_id={run_id}\nbackend=classical\nseed={seed}\n")
            for t in range(1, horizon + 1):
                noise = np.random.normal(0, 0.05)
                sigma_t = max(0.0, min(1.0, sigma[-1] + noise))
                cap_t = max(0.1, capacity[-1] + 0.1 * (0.5 - sigma_t) + noise)
                sigma.append(sigma_t)
                capacity.append(cap_t)
                anomaly_idx.append(
                    max(0.0, min(1.0, np.random.beta(2, 5) + 0.1 * (1 - sigma_t)))
                )
                if t % max(1, horizon // 5) == 0:
                    logf.write(f"t={t} sigma={sigma_t:.3f} cap={cap_t:.3f}\n")

        # Save timeseries
        np.savez(
            result_dir / "timeseries.npz",
            sigma=np.array(sigma),
            capacity=np.array(capacity),
            anomaly=np.array(anomaly_idx),
            dt=dt,
        )
        metrics = {
            "sigma_mean": float(np.mean(sigma)),
            "capacity_mean": float(np.mean(capacity)),
            "anomaly_mean": float(np.mean(anomaly_idx)),
            "sigma_std": float(np.std(sigma)),
            "capacity_std": float(np.std(capacity)),
        }
        metrics_path = result_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        return RunResult(
            run_id=run_id,
            status="ok",
            metrics=metrics,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.CLASSICAL,
        )

    def _run_quantum_stub(
        self,
        cfg: Dict[str, Any],
        run_id: str,
        log_path: Path,
        result_dir: Path,
    ) -> RunResult:
        with log_path.open("w", encoding="utf-8") as logf:
            logf.write("Quantum backend stub\n")
            logf.write(f"run_id={run_id}\n")
            logf.write(f"config={json.dumps(cfg)}\n")
            logf.write("TODO: integrate with quantum framework.\n")
        metrics = {"note": "quantum backend stub only"}
        (result_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return RunResult(
            run_id=run_id,
            status="stub",
            metrics=metrics,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.QUANTUM,
        )
