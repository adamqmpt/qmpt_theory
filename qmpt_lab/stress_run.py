from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime, timezone
import sys

# Allow execution both as module (`python -m qmpt_lab.stress_run`) and as script (`python qmpt_lab/stress_run.py`).
ROOT = Path(__file__).resolve().parent
if str(ROOT.parent) not in sys.path:
    sys.path.append(str(ROOT.parent))

try:  # pragma: no cover
    from qmpt_lab.advanced.agent import AgentConfig
    from qmpt_lab.advanced.runner import RunnerConfig, SimulationRunner
    from qmpt_lab.advanced.world import WorldConfig
except ImportError:  # pragma: no cover
    from .advanced.agent import AgentConfig
    from .advanced.runner import RunnerConfig, SimulationRunner
    from .advanced.world import WorldConfig


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="QMPT Lab Advanced Simulation v2 stress runner")
    p.add_argument("--world-size", type=int, nargs=2, default=[32, 32], help="Width Height")
    p.add_argument("--n-layers", type=int, default=2)
    p.add_argument("--n-agents", type=int, default=8)
    p.add_argument("--episode-length", type=int, default=200)
    p.add_argument("--n-episodes", type=int, default=5)
    p.add_argument("--parallel-worlds", type=int, default=1)
    p.add_argument("--internal-dim", type=int, default=64)
    p.add_argument("--self-model-dim", type=int, default=32)
    p.add_argument("--hidden-dim", type=int, default=128)
    p.add_argument("--horizon-clone", type=int, default=100)
    p.add_argument("--transfer-noise-std", type=float, default=0.05)
    p.add_argument("--continuity-threshold", type=float, default=0.95)
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--log-dir", type=Path, default=Path("qmpt_lab/logs"))
    p.add_argument("--calibrate-target-sec", type=float, default=None, help="If set, auto-scale episodes to target seconds (~10)")
    return p.parse_args()


def main():
    args = parse_args()
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%S")
    # Compute observation dimension based on world view/window and extra signals.
    view_radius = 2
    view_size = (2 * view_radius + 1) ** 2 * 3
    obs_dim = view_size + args.n_layers + 4  # global (3) + neighbor count (1)
    world_cfg = WorldConfig(
        width=args.world_size[0],
        height=args.world_size[1],
        n_layers=args.n_layers,
        n_agents=args.n_agents,
        seed=args.seed,
        view_radius=view_radius,
    )
    agent_cfg = AgentConfig(
        obs_dim=obs_dim,
        internal_dim=args.internal_dim,
        self_model_dim=args.self_model_dim,
        hidden_dim=args.hidden_dim,
        seed=args.seed + 1 if args.seed is not None else None,
    )
    runner_cfg = RunnerConfig(
        world=world_cfg,
        agent=agent_cfg,
        n_episodes=args.n_episodes,
        episode_length=args.episode_length,
        parallel_worlds=args.parallel_worlds,
        horizon_clone=args.horizon_clone,
        transfer_noise_std=args.transfer_noise_std,
        continuity_threshold=args.continuity_threshold,
        run_id=run_id,
        log_dir=str(args.log_dir),
        calibrate_target_sec=args.calibrate_target_sec,
    )
    runner = SimulationRunner(runner_cfg)
    stats = runner.run()
    print(f"[stress_run] run_id={run_id} wall_time={stats['wall_time_sec']:.2f}s eps={runner_cfg.n_episodes}")


if __name__ == "__main__":
    main()
