from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from qmpt_lab.advanced.agent import AgentConfig
from qmpt_lab.advanced.runner import RunnerConfig, SimulationRunner
from qmpt_lab.advanced.world import WorldConfig


def _compute_obs_dim(world_cfg: WorldConfig) -> int:
    r = world_cfg.view_radius
    view_size = (2 * r + 1) ** 2 * 4  # resources, obstacles, portals, cognitive
    return view_size + world_cfg.n_layers + 4  # global signals (3) + neighbor count


def run_high_load_10s(target_runtime_sec: float = 10.0, log_dir: Path | str = "qmpt_lab/logs") -> str:
    """
    Run a high-load QMPT simulation targeting ~10 seconds on an Apple M4-class CPU.
    Returns the run_id.
    """
    # Default heavy config
    world_cfg = WorldConfig(
        width=64,
        height=64,
        n_layers=2,
        n_agents=16,
        obstacle_ratio=0.1,
        resource_ratio=0.08,
        view_radius=3,
        respawn_prob=0.01,
        portal_ratio=0.02,
        seed=12345,
    )
    agent_cfg = AgentConfig(
        obs_dim=_compute_obs_dim(world_cfg),
        internal_dim=128,
        self_model_dim=64,
        hidden_dim=256,
        action_dim=5,
        seed=12346,
    )

    base_cfg = RunnerConfig(
        world=world_cfg,
        agent=agent_cfg,
        n_episodes=800,
        episode_length=300,
        parallel_worlds=8,
        horizon_clone=150,
        transfer_noise_grid=(0.0, 0.01, 0.05, 0.1),
        continuity_threshold=0.95,
        clone_agents_limit=4,
        transfer_agents_limit=4,
        run_id=datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%S"),
        log_dir=str(log_dir),
    )

    # Calibration
    calib_eps = 10
    calib_cfg = RunnerConfig(
        world=world_cfg,
        agent=agent_cfg,
        n_episodes=calib_eps,
        episode_length=100,  # shorter for calibration speed
        parallel_worlds=base_cfg.parallel_worlds,
        horizon_clone=50,
        transfer_noise_grid=base_cfg.transfer_noise_grid,
        continuity_threshold=base_cfg.continuity_threshold,
        clone_agents_limit=min(2, base_cfg.clone_agents_limit),
        transfer_agents_limit=min(2, base_cfg.transfer_agents_limit),
        run_id=base_cfg.run_id + "_calib",
        log_dir=str(log_dir),
    )
    calib_runner = SimulationRunner(calib_cfg)
    start = time.perf_counter()
    calib_runner.run(write_logs=False)
    calib_time = time.perf_counter() - start
    eps_per_sec = calib_eps / max(calib_time, 1e-6)
    # Adjust for longer main episode length vs calibration
    length_scale = calib_cfg.episode_length / base_cfg.episode_length

    # Derive target episodes
    min_eps = 10
    target_eps = int(max(min_eps, target_runtime_sec * eps_per_sec * length_scale))
    main_cfg = base_cfg
    main_cfg.n_episodes = target_eps

    runner = SimulationRunner(main_cfg)
    stats = runner.run(write_logs=True)
    print(
        f"[high_load] run_id={main_cfg.run_id} wall_time={stats['wall_time_sec']:.2f}s "
        f"episodes={main_cfg.n_episodes} target={target_runtime_sec}s"
    )
    return main_cfg.run_id


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run high-load QMPT simulation targeting ~10s runtime.")
    parser.add_argument("--target-runtime-sec", type=float, default=10.0)
    parser.add_argument("--log-dir", type=Path, default=Path("qmpt_lab/logs"))
    args = parser.parse_args()
    run_high_load_10s(args.target_runtime_sec, log_dir=args.log_dir)
