from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import List

import numpy as np

# Allow running as script or module.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

try:  # pragma: no cover
    from .agent import PatternAgent
    from .config import (
        AGENT_CONFIG,
        COPY_HORIZON,
        ENV_CONFIG,
        N_RUNS,
        RUN_SEEDS,
        TRANSFER_HORIZON,
    )
    from .env import GridWorldEnv
    from .experiments import copy_experiment, run_episode, transfer_experiment
    from .metrics import awareness_summary, continuity_cosine
except ImportError:  # pragma: no cover
    from agent import PatternAgent
    from config import (
        AGENT_CONFIG,
        COPY_HORIZON,
        ENV_CONFIG,
        N_RUNS,
        RUN_SEEDS,
        TRANSFER_HORIZON,
    )
    from env import GridWorldEnv
    from experiments import copy_experiment, run_episode, transfer_experiment
    from metrics import awareness_summary, continuity_cosine


def _env_factory(seed):
    return GridWorldEnv(size=ENV_CONFIG["size"], max_steps=ENV_CONFIG["max_steps"], seed=seed)


def run_suite():
    logs_dir = Path(__file__).resolve().parent / "logs"
    results_dir = Path(__file__).resolve().parent / "results"
    logs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    run_records = []
    for idx in range(N_RUNS):
        seed = RUN_SEEDS[idx % len(RUN_SEEDS)]
        env = _env_factory(seed)
        agent_cfg = AGENT_CONFIG.copy()
        agent_cfg["seed"] = seed
        agent = PatternAgent(obs_dim=env.obs_dim, internal_dim=agent_cfg["internal_dim"], self_model_dim=agent_cfg["self_model_dim"], seed=agent_cfg["seed"])

        ep = run_episode(env, agent, max_steps=ENV_CONFIG["max_steps"])
        cont_mid_final = continuity_cosine(ep["pattern_mid"], ep["pattern_final"])
        awareness_before = awareness_summary(ep["awareness"])

        # copy experiment uses observation sequence after mid
        obs_after_mid = ep["observations"][ep["mid_step"] :]
        copy_res = copy_experiment(obs_after_mid, ep["pattern_mid"], PatternAgent, horizon=COPY_HORIZON)

        # transfer experiment with fresh env
        transfer_res = transfer_experiment(lambda: _env_factory(seed + 1000), ep["pattern_mid"], PatternAgent, horizon=TRANSFER_HORIZON)

        run_id = f"run_{idx+1:03d}"
        record = {
            "run_id": run_id,
            "seed": seed,
            "env": ENV_CONFIG,
            "agent": agent_cfg,
            "metrics": {
                "continuity": {
                    "mid_to_final": cont_mid_final,
                    "mid_to_transferred": transfer_res["continuity_mid_to_transferred"],
                },
                "behavior": {
                    "copy_divergence": copy_res["copy_divergence"],
                    "transfer_divergence": transfer_res["behavior_divergence_transfer_vs_baseline"],
                },
                "awareness": {
                    "mean_before_transfer": awareness_before,
                    "mean_after_transfer": transfer_res["awareness_after"],
                },
            },
            "episode": {
                "length": len(ep["actions"]),
                "total_reward": float(np.sum(ep["rewards"])),
            },
        }
        run_records.append(record)
        with (logs_dir / f"{run_id}.json").open("w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

    summary = aggregate_results(run_records)
    with (results_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    markdown = summary_markdown(summary)
    with (results_dir / "summary.md").open("w", encoding="utf-8") as f:
        f.write(markdown)
    return run_records


def aggregate_results(records: List[dict]) -> dict:
    metrics = {
        "continuity_mid_to_final": [],
        "continuity_mid_to_transferred": [],
        "behavior_copy_divergence": [],
        "behavior_transfer_divergence": [],
        "awareness_before": [],
        "awareness_after": [],
    }
    for rec in records:
        m = rec["metrics"]
        metrics["continuity_mid_to_final"].append(m["continuity"]["mid_to_final"])
        metrics["continuity_mid_to_transferred"].append(m["continuity"]["mid_to_transferred"])
        metrics["behavior_copy_divergence"].append(m["behavior"]["copy_divergence"])
        metrics["behavior_transfer_divergence"].append(m["behavior"]["transfer_divergence"])
        metrics["awareness_before"].append(m["awareness"]["mean_before_transfer"])
        metrics["awareness_after"].append(m["awareness"]["mean_after_transfer"])

    def stats(vals):
        if not vals:
            return {"values": [], "mean": None, "std": None}
        return {"values": vals, "mean": mean(vals), "std": pstdev(vals) if len(vals) > 1 else 0.0}

    metrics_stats = {k: stats(v) for k, v in metrics.items()}
    return {
        "test_name": "qmpt_pattern_transfer_v1",
        "n_runs": len(records),
        "metrics": metrics_stats,
        "runs": records,
    }


def summary_markdown(summary: dict) -> str:
    lines = []
    lines.append("# QMPT Pattern Transfer Test v1")
    lines.append("")
    lines.append("## Overview")
    lines.append("Pattern continuity, copy vs transfer behavior, and self-awareness change across 5 fixed runs.")
    lines.append("")
    lines.append("## Run Metrics")
    lines.append("| Run | Seed | C(mid→final) | C(mid→transfer) | Copy divergence | Transfer divergence | Awareness before | Awareness after |")
    lines.append("|-----|------|--------------|-----------------|-----------------|--------------------|------------------|-----------------|")
    for rec in summary["runs"]:
        m = rec["metrics"]
        lines.append(
            f"| {rec['run_id']} | {rec['seed']} | "
            f"{m['continuity']['mid_to_final']:.4f} | "
            f"{m['continuity']['mid_to_transferred']:.4f} | "
            f"{m['behavior']['copy_divergence']:.4f} | "
            f"{m['behavior']['transfer_divergence']:.4f} | "
            f"{m['awareness']['mean_before_transfer']:.4f} | "
            f"{m['awareness']['mean_after_transfer']:.4f} |"
        )
    lines.append("")
    lines.append("## Aggregated Results")
    for name, stats in summary["metrics"].items():
        lines.append(f"- {name}: mean={stats['mean']:.4f} std={stats['std']:.4f}")
    lines.append("")
    lines.append("## Notes")
    lines.append("Initial automated sweep; metrics are illustrative and model-specific.")
    return "\n".join(lines)


if __name__ == "__main__":
    run_suite()
