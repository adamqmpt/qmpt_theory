"""
Simulation runner abstraction with classical and quantum backends.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Protocol

from .state import repo_root
from code.qmpt_core import scenarios, io as core_io


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


class Backend(Protocol):
    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        ...


class ClassicalBackend:
    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        with log_path.open("w", encoding="utf-8") as logf:
            logf.write(f"run_id={run_id}\nbackend=classical\n")
            logf.write(f"config={json.dumps(cfg)}\n")

        layer, summary = scenarios.run_scenario(cfg)
        core_io.save_run_results(run_id, layer, summary, result_dir)
        return RunResult(
            run_id=run_id,
            status="ok",
            metrics=summary,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.CLASSICAL,
        )


class QuantumBackendStub:
    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        metrics = {
            "backend": "quantum_stub",
            "status": "not_implemented",
            "note": "Quantum backend stub only",
        }
        with log_path.open("w", encoding="utf-8") as logf:
            logf.write("Quantum backend stub\n")
            logf.write(f"run_id={run_id}\n")
            logf.write(f"config={json.dumps(cfg)}\n")
            if "quantum" in cfg:
                qcfg = cfg["quantum"]
                program_path = qcfg.get("program_path")
                logf.write(f"program_path={program_path}\n")
        (result_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return RunResult(
            run_id=run_id,
            status="stub",
            metrics=metrics,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.QUANTUM,
        )


class SimulationRunner:
    """
    Dispatches simulations based on backend. Classical uses qmpt_core scenarios;
    quantum is a stub for future integration.
    """

    def __init__(self, registry) -> None:
        self.registry = registry
        self.backends: Dict[BackendType, Backend] = {
            BackendType.CLASSICAL: ClassicalBackend(),
            BackendType.QUANTUM: QuantumBackendStub(),
        }

    def run(self, config_path: Path, backend: BackendType) -> RunResult:
        cfg = self._load_experiment_config(config_path)
        cfg.setdefault("scenario", "baseline_layer")
        run_id = self._generate_run_id(config_path, cfg)
        base = repo_root()
        logs_dir = base / cfg.get("logs_dir", "lab/logs")
        results_root = base / cfg.get("results_dir", "lab/results")
        logs_dir.mkdir(parents=True, exist_ok=True)
        results_root.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"{run_id}.log"
        result_dir = results_root / run_id
        result_dir.mkdir(parents=True, exist_ok=True)

        backend_impl = self.backends.get(backend, QuantumBackendStub())
        return backend_impl.run(run_id, cfg, log_path, result_dir)

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
