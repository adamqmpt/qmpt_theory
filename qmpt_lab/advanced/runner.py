from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from pathlib import Path

from .agent import AgentConfig, PatternAgentAdv
from .logger import JSONLLogger, LogConfig
from .metrics import behavior_divergence, cosine_continuity
from .world import MultiLayerWorld, WorldConfig


@dataclass
class RunnerConfig:
    world: WorldConfig
    agent: AgentConfig
    n_episodes: int = 10
    episode_length: int = 200
    parallel_worlds: int = 1
    horizon_clone: int = 100
    transfer_noise_grid: Tuple[float, ...] = (0.0, 0.01, 0.05, 0.1)
    continuity_threshold: float = 0.95
    clone_agents_limit: int = 4
    transfer_agents_limit: int = 4
    run_id: str = "run"
    log_dir: str = "qmpt_lab/logs"
    calibrate_target_sec: float | None = None  # if set, adjust n_episodes to target runtime


class SimulationRunner:
    def __init__(self, cfg: RunnerConfig):
        self.cfg = cfg
        self.logger = JSONLLogger(LogConfig(log_dir=Path(cfg.log_dir), run_id=cfg.run_id))

    def run(self, write_logs: bool = True):
        logger = self.logger if write_logs else _NullLogger()
        meta = self._meta_record()
        logger.write_jsonl(meta)

        start = time.perf_counter()
        total_steps = 0
        summary_rows = []

        for ep in range(self.cfg.n_episodes):
            # deterministic seed per episode for baseline/anomaly comparison
            ep_seed = (self.cfg.world.seed or 0) + ep
            world = MultiLayerWorld(self.cfg.world)
            world.reset(seed=ep_seed)
            agents = {aid: PatternAgentAdv(self.cfg.agent) for aid in range(self.cfg.world.n_agents)}
            observations = world._build_observations()

            pattern_state_mid = {}
            mid_t = self.cfg.episode_length // 2
            world_state_mid = None
            info = {}

            # baseline roll
            for t in range(self.cfg.episode_length):
                actions = {}
                for aid, agent in agents.items():
                    actions[aid] = agent.policy(observations[aid])
                observations, rewards, _, info = world.step(actions)
                if t == mid_t:
                    world_state_mid = world.get_state()
                    for aid, agent in agents.items():
                        pattern_state_mid[aid] = agent.get_pattern_state()
                total_steps += 1

            pattern_state_final = {aid: agent.get_pattern_state() for aid, agent in agents.items()}

            # continuity logs and summary seed row
            for aid in agents:
                cont = cosine_continuity(
                    _flatten_pattern(pattern_state_mid[aid]),
                    _flatten_pattern(pattern_state_final[aid]),
                )
                rec = {
                    "type": "pattern_continuity",
                    "run_id": self.cfg.run_id,
                    "episode_id": ep,
                    "agent_id": aid,
                    "t_mid": mid_t,
                    "t_final": self.cfg.episode_length,
                    "continuity_mid_to_final": cont,
                }
                logger.write_jsonl(rec)
                summary_rows.append(
                    {
                        "run_id": self.cfg.run_id,
                        "episode_id": ep,
                        "agent_id": aid,
                        "continuity_mid_to_final": cont,
                        "transfer_noise_std": "",
                    }
                )

            # clone divergence for subset
            subset_agents = list(agents.keys())[: self.cfg.clone_agents_limit]
            for aid in subset_agents:
                clone_a = PatternAgentAdv.from_pattern_state(self.cfg.agent, pattern_state_mid[aid], transfer_noise_std=0.0)
                clone_b = PatternAgentAdv.from_pattern_state(self.cfg.agent, pattern_state_mid[aid], transfer_noise_std=0.0)
                # use mid-state world snapshot to generate observations
                world_clone = MultiLayerWorld(self.cfg.world)
                if world_state_mid is not None:
                    world_clone.set_state(world_state_mid)
                obs_clone = world_clone._build_observations()
                acts_a, acts_b = [], []
                for _ in range(self.cfg.horizon_clone):
                    act_a = clone_a.policy(obs_clone[aid])
                    act_b = clone_b.policy(obs_clone[aid])
                    acts_a.append(act_a)
                    acts_b.append(act_b)
                    obs_clone, _, _, _ = world_clone.step({aid: act_a})
                div = behavior_divergence(acts_a, acts_b)
                rec = {
                    "type": "clone_divergence",
                    "run_id": self.cfg.run_id,
                    "episode_id": ep,
                    "agent_id": aid,
                    "horizon": self.cfg.horizon_clone,
                    "behavior_divergence_mid_copies": div,
                }
                logger.write_jsonl(rec)
                summary_rows.append(
                    {
                        "run_id": self.cfg.run_id,
                        "episode_id": ep,
                        "agent_id": aid,
                        "clone_divergence": div,
                        "transfer_noise_std": "",
                    }
                )

            # transfer tests for subset and noise grid
            transfer_agents = list(agents.keys())[: self.cfg.transfer_agents_limit]
            for aid in transfer_agents:
                for noise in self.cfg.transfer_noise_grid:
                    transferred = PatternAgentAdv.from_pattern_state(
                        self.cfg.agent, pattern_state_mid[aid], transfer_noise_std=noise
                    )
                    baseline_agent = PatternAgentAdv.from_pattern_state(
                        self.cfg.agent, pattern_state_mid[aid], transfer_noise_std=0.0
                    )
                    cont_transfer = cosine_continuity(
                        _flatten_pattern(pattern_state_mid[aid]),
                        _flatten_pattern(transferred.get_pattern_state()),
                    )
                    world_trans = MultiLayerWorld(self.cfg.world)
                    world_trans.reset(seed=ep_seed + 999)  # different seed for transfer world
                    obs_trans = world_trans._build_observations()
                    acts_trans, acts_base = [], []
                    for _ in range(self.cfg.horizon_clone):
                        act_t = transferred.policy(obs_trans[aid])
                        act_b = baseline_agent.policy(obs_trans[aid])
                        acts_trans.append(act_t)
                        acts_base.append(act_b)
                        obs_trans, _, _, _ = world_trans.step({aid: act_t})
                    div_transfer = behavior_divergence(acts_trans, acts_base)
                    rec = {
                        "type": "transfer_event",
                        "run_id": self.cfg.run_id,
                        "episode_id": ep,
                        "agent_id": aid,
                        "t_mid": mid_t,
                        "target_world_id": f"world_ep{ep}_noise{noise}",
                        "transfer_noise_std": noise,
                        "continuity_mid_to_transferred": cont_transfer,
                        "behavior_divergence_transfer_vs_baseline": div_transfer,
                    }
                    logger.write_jsonl(rec)
                    summary_rows.append(
                        {
                            "run_id": self.cfg.run_id,
                            "episode_id": ep,
                            "agent_id": aid,
                            "continuity_mid_to_transferred": cont_transfer,
                            "behavior_divergence_transfer_vs_baseline": div_transfer,
                            "transfer_noise_std": noise,
                        }
                    )

            # anomaly impact vs no-agent baseline
            no_agent_world = MultiLayerWorld(self.cfg.world)
            no_agent_world.reset(seed=ep_seed)
            for _ in range(self.cfg.episode_length):
                no_agent_world.step({})
            baseline_resources = no_agent_world.resources.astype(np.float32)
            delta_res = world.resources.astype(np.float32) - baseline_resources
            anomaly_score = float(np.linalg.norm(delta_res) / max(self.cfg.world.width * self.cfg.world.height, 1))
            rec = {
                "type": "anomaly_impact",
                "run_id": self.cfg.run_id,
                "episode_id": ep,
                "agent_id": -1,
                "anomaly_score": anomaly_score,
                "metric_def": "delta resource distribution L2-normalized by grid size",
            }
            logger.write_jsonl(rec)
            summary_rows.append(
                {
                    "run_id": self.cfg.run_id,
                    "episode_id": ep,
                    "agent_id": -1,
                    "anomaly_score": anomaly_score,
                    "transfer_noise_std": "",
                }
            )

        wall_time = time.perf_counter() - start
        runtime_row = {
            "type": "runtime_stats",
            "run_id": self.cfg.run_id,
            "wall_time_sec": wall_time,
            "total_episodes": self.cfg.n_episodes,
            "steps_per_second": total_steps / max(wall_time, 1e-6),
            "cpu_utilization_approx": 0.0,
        }
        logger.write_jsonl(runtime_row)
        if write_logs and summary_rows:
            logger.write_csv_rows(summary_rows)
        logger.close()
        return runtime_row

    def _meta_record(self) -> dict:
        return {
            "type": "run_meta",
            "run_id": self.cfg.run_id,
            "timestamp": time.time(),
            "config": {
                "world_size": [self.cfg.world.width, self.cfg.world.height],
                "n_layers": self.cfg.world.n_layers,
                "n_agents": self.cfg.world.n_agents,
                "episode_length": self.cfg.episode_length,
                "n_episodes": self.cfg.n_episodes,
                "parallel_worlds": self.cfg.parallel_worlds,
                "internal_dim": self.cfg.agent.internal_dim,
                "self_model_dim": self.cfg.agent.self_model_dim,
                "policy_hidden_dim": self.cfg.agent.hidden_dim,
                "transfer_noise_grid": list(self.cfg.transfer_noise_grid),
                "clone_horizon": self.cfg.horizon_clone,
                "transfer_agents_limit": self.cfg.transfer_agents_limit,
                "clone_agents_limit": self.cfg.clone_agents_limit,
                "rng_seed": self.cfg.world.seed,
            },
        }


def _flatten_pattern(pattern_state: Dict[str, np.ndarray]) -> np.ndarray:
    parts = []
    for key in ("internal_state", "self_model_state", "Wp1", "bp1", "Wp2", "bp2", "Ws1", "bs1", "Ws2", "bs2"):
        arr = pattern_state[key]
        parts.append(arr.astype(np.float64).ravel())
    return np.concatenate(parts)


class _NullLogger:
    def write_jsonl(self, record: dict):
        pass

    def write_csv_rows(self, rows):
        pass

    def close(self):
        pass
