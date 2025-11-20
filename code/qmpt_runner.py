"""
Headless CLI runner for QMPT Lab experiments (single or ensemble).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime

from code.qmpt_ide.sim_runner import SimulationRunner, BackendType
from code.qmpt_ide.core_runs import RunRegistry, RunRecord
from code.qmpt_ide.state import repo_root


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="QMPT Lab CLI runner")
    p.add_argument("--config", required=True, help="Path to config JSON")
    p.add_argument("--backend", choices=[b.value for b in BackendType], help="Override backend")
    p.add_argument("--ensemble-enabled", action="store_true", help="Force ensemble mode")
    p.add_argument("--n-runs", type=int, help="Ensemble repeat count override")
    p.add_argument("--dataset-description", type=str, default="", help="Dataset description")
    p.add_argument("--executor", choices=["local_sequential", "local_parallel"], help="Executor override")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    config_path = (repo_root() / args.config).resolve()
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if args.backend:
        cfg["backend"] = args.backend
    if args.executor:
        cfg.setdefault("executor", {})["type"] = args.executor
    if args.ensemble_enabled or cfg.get("ensemble", {}).get("enabled"):
        cfg.setdefault("ensemble", {})
        cfg["ensemble"]["enabled"] = True
        if args.n_runs:
            cfg["ensemble"]["n_runs"] = args.n_runs
        if args.dataset_description:
            cfg["ensemble"]["description"] = args.dataset_description
    backend = BackendType(cfg.get("backend", args.backend or "classical"))

    registry_path = repo_root() / cfg.get("registry_path", "lab/runs.jsonl")
    registry = RunRegistry(registry_path)
    runner = SimulationRunner(registry)
    if cfg.get("ensemble", {}).get("enabled"):
        dataset_id, results = runner.run_ensemble(config_path, backend, cfg.get("ensemble"), base_cfg=cfg)
        for res in results:
            registry.add(_to_record(res, config_path))
        print(f"Ensemble done: dataset_id={dataset_id}, runs={len(results)}")
        print(f"Dataset manifest: lab/datasets/{dataset_id}/dataset_manifest.json")
    else:
        res = runner.run_config(cfg, backend, config_path=config_path)
        registry.add(_to_record(res, config_path))
        print(f"Run done: run_id={res.run_id}, backend={res.backend.value}, status={res.status}")
        print(f"Results: {res.results_path}")


def _to_record(result, config_path: Path) -> RunRecord:
    return RunRecord(
        run_id=result.run_id,
        timestamp=datetime.utcnow().timestamp(),
        config_path=str(config_path),
        backend=result.backend.value,
        status=result.status,
        log_path=str(result.log_path),
        results_path=str(result.results_path),
        metrics=result.metrics,
        git_commit=result.git_commit,
        config_hash=result.config_hash,
        dataset_id=result.dataset_id,
    )


if __name__ == "__main__":
    main()
