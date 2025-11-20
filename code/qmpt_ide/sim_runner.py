"""
Simulation runner abstraction with classical, quantum, hybrid backends and ensemble support.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Protocol, Optional, List, Tuple

import numpy as np

from code.qmpt_core import scenarios as classical_scenarios, io as core_io, metrics as core_metrics
from .quantum import scenarios as quantum_scenarios
from .quantum.backends import LocalSimulatorBackend, DummyQuantumBackend, QuantumBackend
from .quantum.encodings import layer_to_circuit
from .state import repo_root


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
    dataset_id: Optional[str] = None


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
        core_io.save_run_results(run_id, layer, summary, result_dir, cfg)
        metrics = json.loads((result_dir / "metrics.json").read_text(encoding="utf-8"))
        return RunResult(
            run_id=run_id,
            status="ok",
            metrics=metrics,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.CLASSICAL,
        )


class QuantumBackendWrapper:
    """Wraps quantum scenarios with a real or dummy backend."""

    def __init__(self) -> None:
        self.engine: QuantumBackend = LocalSimulatorBackend()
        if not getattr(self.engine, "is_available", True):
            self.engine = DummyQuantumBackend()

    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        summary, timeseries = quantum_scenarios.run_quantum_scenario(cfg, self.engine, log_path, result_dir)
        summary["backend"] = "quantum_local" if self.engine.is_available else "quantum_dummy"
        self._write_results(result_dir, timeseries, summary, cfg)
        metrics = json.loads((result_dir / "metrics.json").read_text(encoding="utf-8"))
        status = summary.get("status", "ok" if self.engine.is_available else "unavailable")
        return RunResult(
            run_id=run_id,
            status=status,
            metrics=metrics,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.QUANTUM,
        )

    def _write_results(self, result_dir: Path, timeseries: Dict[str, Any], summary: Dict[str, Any], cfg: Dict[str, Any]) -> None:
        result_dir.mkdir(parents=True, exist_ok=True)
        np.savez(result_dir / "timeseries.npz", **timeseries)
        derived = core_metrics.compute_run_metrics(timeseries, cfg)
        merged = {**summary, **derived}
        (result_dir / "metrics.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")


class HybridBackend:
    """
    Hybrid classical-quantum cycle: classical layer dynamics probed by quantum circuit,
    with probe influencing subsequent classical evolution.
    """

    def __init__(self) -> None:
        self.q_backend: QuantumBackend = LocalSimulatorBackend()
        if not getattr(self.q_backend, "is_available", True):
            self.q_backend = DummyQuantumBackend()

    def run(self, run_id: str, cfg: Dict[str, Any], log_path: Path, result_dir: Path) -> RunResult:
        with log_path.open("w", encoding="utf-8") as logf:
            logf.write("Hybrid backend\n")
            logf.write(f"run_id={run_id}\n")
            logf.write(f"config={json.dumps(cfg)}\n")

        horizon = int(cfg.get("horizon", 50))
        dt = float(cfg.get("dt", 1.0))
        seed = int(cfg.get("seed", 42))
        probe_every = int(cfg.get("probe_interval", cfg.get("hybrid", {}).get("probe_interval", 5)))
        rng = np.random.default_rng(seed)

        stress = 0.3
        protection = 0.8
        novelty = 0.2

        t_arr = []
        stress_arr = []
        protection_arr = []
        novelty_arr = []
        expectation_arr = []
        entropy_arr = []
        anomaly_arr = []

        for step in range(horizon):
            t = step * dt
            # Classical update (simple drift with anomaly coupling)
            stress = float(np.clip(stress + rng.normal(0, 0.04), 0.0, 1.0))
            protection = float(np.clip(protection + rng.normal(0, 0.02), 0.0, 1.0))
            novelty = float(np.clip(novelty + rng.normal(0, 0.03), 0.0, 1.0))
            anomaly_proxy = 0.0

            # Quantum probe
            exp_mean = 0.0
            ent = 0.0
            if step % probe_every == 0 and getattr(self.q_backend, "is_available", True):
                circuit = layer_to_circuit({"stress": stress, "novelty": novelty}, n_qubits=3, depth=2, anomaly=stress, seed=seed + step)
                qres = self.q_backend.run_circuit(circuit, shots=int(cfg.get("quantum", {}).get("shots", 256)), seed=seed + step)
                if qres.expectations:
                    exp_mean = float(np.mean(list(qres.expectations.values())))
                ent = float(qres.entropy)
                anomaly_proxy = float(np.clip(0.5 * (1.0 - exp_mean) + 0.5 * ent / np.log2(8), 0.0, 1.0))
                # Feed back into classical state
                stress = float(np.clip(stress + 0.1 * anomaly_proxy, 0.0, 1.0))
                protection = float(np.clip(protection - 0.05 * anomaly_proxy, 0.0, 1.0))
            else:
                anomaly_proxy = float(np.clip(0.1 + 0.05 * stress, 0.0, 1.0))
            t_arr.append(t)
            stress_arr.append(stress)
            protection_arr.append(protection)
            novelty_arr.append(novelty)
            expectation_arr.append(exp_mean)
            entropy_arr.append(ent)
            anomaly_arr.append(anomaly_proxy)

        timeseries = {
            "t": np.array(t_arr, dtype=float),
            "stress": np.array(stress_arr, dtype=float),
            "protection": np.array(protection_arr, dtype=float),
            "novelty": np.array(novelty_arr, dtype=float),
            "expectation_mean": np.array(expectation_arr, dtype=float),
            "entropy": np.array(entropy_arr, dtype=float),
            "anomaly_proxy": np.array(anomaly_arr, dtype=float),
        }
        summary = {
            "backend": "hybrid",
            "seed": seed,
            "horizon": horizon,
            "probe_interval": probe_every,
        }
        result_dir.mkdir(parents=True, exist_ok=True)
        np.savez(result_dir / "timeseries.npz", **timeseries)
        derived = core_metrics.compute_run_metrics(timeseries, cfg)
        summary.update(derived)
        (result_dir / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        status = "ok" if getattr(self.q_backend, "is_available", True) else "degraded"
        return RunResult(
            run_id=run_id,
            status=status,
            metrics=summary,
            log_path=log_path,
            results_path=result_dir,
            backend=BackendType.HYBRID,
        )


class SimulationRunner:
    """
    Dispatches simulations based on backend. Supports single runs and ensembles.
    """

    def __init__(self, registry=None) -> None:
        self.registry = registry
        self.backends: Dict[BackendType, Backend] = {
            BackendType.CLASSICAL: ClassicalBackend(),
            BackendType.QUANTUM: QuantumBackendWrapper(),
            BackendType.HYBRID: HybridBackend(),
        }

    # ---- Public API ----
    def run(self, config_path: Path, backend: BackendType) -> RunResult:
        cfg = self._load_experiment_config(config_path)
        return self.run_config(cfg, backend, config_path=config_path)

    def run_config(self, cfg: Dict[str, Any], backend: BackendType, config_path: Optional[Path] = None, dataset_id: Optional[str] = None) -> RunResult:
        cfg = copy.deepcopy(cfg)
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

        backend_impl = self.backends.get(backend, HybridBackend())
        result = backend_impl.run(run_id, cfg, log_path, result_dir)
        result.git_commit = self._safe_git_commit()
        result.config_hash = self._config_hash(cfg)
        result.dataset_id = dataset_id
        return result

    def run_ensemble(self, config_path: Path, backend: BackendType, overrides: Optional[Dict[str, Any]] = None, base_cfg: Optional[Dict[str, Any]] = None) -> Tuple[str, List[RunResult]]:
        cfg = copy.deepcopy(base_cfg) if base_cfg is not None else self._load_experiment_config(config_path)
        if overrides:
            cfg.setdefault("ensemble", {})
            cfg["ensemble"].update(overrides)
        ensemble_cfg = cfg.get("ensemble", {})
        if not ensemble_cfg.get("enabled"):
            # fallback to single run
            single = self.run_config(cfg, backend, config_path=config_path)
            return "", [single]

        dataset_id = ensemble_cfg.get("dataset_id") or self._generate_dataset_id()
        base = repo_root()
        datasets_root = base / "lab" / "datasets" / dataset_id
        datasets_root.mkdir(parents=True, exist_ok=True)
        base_config_rel = str(config_path.relative_to(base)) if config_path else "inline"

        run_cfgs = self._expand_ensemble(cfg)
        executor_type = cfg.get("executor", {}).get("type", "local_sequential")
        max_workers = int(cfg.get("executor", {}).get("max_workers", 4))
        results: List[RunResult] = []
        if executor_type == "local_parallel" and len(run_cfgs) > 1:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(self.run_config, rcfg, BackendType(rcfg.get("backend", backend.value)), config_path, dataset_id) for rcfg in run_cfgs]
                for fut in futures:
                    results.append(fut.result())
        else:
            for rcfg in run_cfgs:
                results.append(self.run_config(rcfg, BackendType(rcfg.get("backend", backend.value)), config_path, dataset_id))

        self._write_dataset_manifest(datasets_root, dataset_id, base_config_rel, cfg, results)
        return dataset_id, results

    # ---- Helpers ----
    def _write_dataset_manifest(self, ds_root: Path, dataset_id: str, base_config: str, base_cfg: Dict[str, Any], results: List[RunResult]) -> None:
        manifest = {
            "dataset_id": dataset_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_commit": self._safe_git_commit(),
            "description": base_cfg.get("ensemble", {}).get("description", ""),
            "config_template": base_config,
            "runs": [],
        }
        metrics_list = []
        for r in results:
            entry = {
                "run_id": r.run_id,
                "backend": r.backend.value,
                "scenario": base_cfg.get("scenario"),
                "seed": r.metrics.get("seed", base_cfg.get("seed")),
                "params": {},
                "metrics_path": str(r.results_path / "metrics.json"),
                "timeseries_path": str(r.results_path / "timeseries.npz"),
            }
            manifest["runs"].append(entry)
            metrics_list.append(r.metrics)
        ds_root.mkdir(parents=True, exist_ok=True)
        (ds_root / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        ensemble_metrics = core_metrics.compute_ensemble_summary(metrics_list)
        (ds_root / "ensemble_metrics.json").write_text(json.dumps(ensemble_metrics, indent=2), encoding="utf-8")

    def _expand_ensemble(self, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        ens = cfg.get("ensemble", {})
        mode = ens.get("mode", "repeat")
        run_cfgs: List[Dict[str, Any]] = []
        if mode == "sweep":
            grid = ens.get("param_grid", {})
            keys = list(grid.keys())
            values = [grid[k] for k in keys]
            for combo in itertools.product(*values):
                rcfg = copy.deepcopy(cfg)
                for k, v in zip(keys, combo):
                    rcfg[k] = v
                run_cfgs.append(rcfg)
        else:  # repeat
            n_runs = int(ens.get("n_runs", 1))
            base_seed = int(cfg.get("seed", 42))
            for i in range(n_runs):
                rcfg = copy.deepcopy(cfg)
                rcfg["seed"] = base_seed + i
                run_cfgs.append(rcfg)
        return run_cfgs

    def _load_experiment_config(self, path: Path) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _generate_run_id(self, config_path: Optional[Path], cfg: Dict[str, Any]) -> str:
        seed = cfg.get("seed", 42)
        backend = cfg.get("backend", "classical")
        payload = f"{config_path}-{seed}-{backend}-{time.time()}"
        return hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]

    def _generate_dataset_id(self) -> str:
        return uuid.uuid4().hex[:12]

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
