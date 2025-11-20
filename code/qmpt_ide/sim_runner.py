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
from typing import Dict, Any, Protocol, Optional

from .state import repo_root
from code.qmpt_core import scenarios as classical_scenarios, io as core_io
from .quantum import scenarios as quantum_scenarios
from .quantum.backends import LocalSimulatorBackend, DummyQuantumBackend, QuantumBackend


class BackendType(str, Enum):
    CLASSICAL = "classical"
    QUANTUM = "quantum"
    HYBRID = "hybrid"


@dataclass
class RunResult:
    run_id: str
    status: str
    metrics: Dict[str, Any]
    log_path: Path
    results_path: Path
    backend: BackendType
    git_commit: Optional[str] = None
    config_hash: Optional[str] = None


class Backend(Protocol):
    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        ...


class ClassicalBackend:
    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        with log_path.open("w", encoding="utf-8") as logf:
            logf.write(f"run_id={run_id}\nbackend=classical\n")
            logf.write(f"config={json.dumps(cfg)}\n")

        layer, summary = classical_scenarios.run_scenario(cfg)
        summary["backend"] = "classical"
        core_io.save_run_results(run_id, layer, summary, result_dir)
        return RunResult(
            run_id=run_id,
            status="ok",
            metrics=summary,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.CLASSICAL,
        )


class QuantumBackendWrapper:
    """Wraps quantum scenarios with a real or dummy backend."""

    def __init__(self) -> None:
        self.engine: QuantumBackend = LocalSimulatorBackend()
        if not self.engine.is_available:
            self.engine = DummyQuantumBackend()

    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        summary = quantum_scenarios.run_quantum_scenario(cfg, self.engine, log_path, result_dir)
        status = summary.get("status", "ok" if self.engine.is_available else "unavailable")
        return RunResult(
            run_id=run_id,
            status=status,
            metrics=summary,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.QUANTUM,
        )


class HybridBackendStub:
    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        note = {
            "backend": "hybrid_stub",
            "status": "not_implemented",
            "reason": "Hybrid backend is planned for a later version.",
        }
        (result_dir / "metrics.json").write_text(json.dumps(note, indent=2), encoding="utf-8")
        with log_path.open("w", encoding="utf-8") as logf:
            logf.write("Hybrid backend stub\n")
            logf.write(f"run_id={run_id}\nconfig={json.dumps(cfg)}\n")
        return RunResult(
            run_id=run_id,
            status="stub",
            metrics=note,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.HYBRID,
        )


class SimulationRunner:
    """
    Dispatches simulations based on backend. Classical uses qmpt_core scenarios;
    quantum uses qiskit-based circuits if available; hybrid is a stub placeholder.
    """

    def __init__(self, registry) -> None:
        self.registry = registry
        self.backends: Dict[BackendType, Backend] = {
            BackendType.CLASSICAL: ClassicalBackend(),
            BackendType.QUANTUM: QuantumBackendWrapper(),
            BackendType.HYBRID: HybridBackendStub(),
        }

    def run(self, config_path: Path, backend: BackendType) -> RunResult:
        cfg = self._load_experiment_config(config_path)
        cfg.setdefault("scenario", "baseline_layer" if backend == BackendType.CLASSICAL else "layer_stress_probe")
        cfg.setdefault("backend", backend.value)
        run_id = self._generate_run_id(config_path, cfg)
        base = repo_root()
        logs_dir = base / cfg.get("logs_dir", "lab/logs")
        results_root = base / cfg.get("results_dir", "lab/results")
        logs_dir.mkdir(parents=True, exist_ok=True)
        results_root.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"{run_id}.log"
        result_dir = results_root / run_id
        result_dir.mkdir(parents=True, exist_ok=True)

        backend_impl = self.backends.get(backend, HybridBackendStub())
        result = backend_impl.run(run_id, cfg, log_path, result_dir)
        result.git_commit = self._safe_git_commit()
        result.config_hash = self._config_hash(cfg)
        return result

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

    def _config_hash(self, cfg: Dict[str, Any]) -> str:
        serialized = json.dumps(cfg, sort_keys=True).encode("utf-8")
        return hashlib.sha1(serialized).hexdigest()[:12]

    def _safe_git_commit(self) -> Optional[str]:
        try:
            head = (repo_root() / ".git" / "HEAD").read_text().strip()
            if head.startswith("ref:"):
                ref_path = repo_root() / ".git" / head.split(" ", 1)[1]
                return ref_path.read_text().strip()[:12]
            return head[:12]
        except Exception:
            return None
