from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np

# Allow running both as module (`python -m qmpt_lab.run_sim`) and as script (`python qmpt_lab/run_sim.py`).
try:  # pragma: no cover - import convenience
    from .agent import PatternAgent
    from .env import GridWorldEnv
    from .metrics import behavior_divergence, continuity_cosine
except ImportError:  # pragma: no cover
    import sys

    ROOT = Path(__file__).resolve().parent.parent
    if str(ROOT) not in sys.path:
        sys.path.append(str(ROOT))
    from qmpt_lab.agent import PatternAgent
    from qmpt_lab.env import GridWorldEnv
    from qmpt_lab.metrics import behavior_divergence, continuity_cosine


LOG_DIR = Path(__file__).resolve().parent / "logs"


@dataclass
class EpisodeResult:
    observations: np.ndarray
    actions: list[int]
    rewards: list[float]

    @property
    def length(self) -> int:
        return len(self.actions)

    def to_log(self) -> dict:
        return {
            "observations": self.observations.tolist(),
            "actions": self.actions,
            "rewards": self.rewards,
        }


def _safe_entropy(probs: np.ndarray) -> float:
    probs = probs[probs > 0]
    if probs.size == 0:
        return 0.0
    return float(-np.sum(probs * np.log(probs + 1e-15)))


def summarize_episode(episode: EpisodeResult, env_size: int) -> dict:
    """Compact summary for downstream analysis."""
    actions = np.array(episode.actions, dtype=np.int64)
    rewards = np.array(episode.rewards, dtype=np.float64)

    unique, counts = np.unique(actions, return_counts=True)
    total_actions = actions.size if actions.size else 1
    dist = {int(k): int(v) for k, v in zip(unique.tolist(), counts.tolist())}
    freqs = {int(k): float(v) / total_actions for k, v in zip(unique.tolist(), counts.tolist())}
    entropy = _safe_entropy(np.array(list(freqs.values()), dtype=np.float64))

    positions = []
    for obs in episode.observations:
        pos = int(np.argmax(obs[:env_size])) if env_size > 0 else 0
        positions.append(pos)

    steps_to_goal = None
    for idx, r in enumerate(rewards):
        if r > 0.0:
            steps_to_goal = idx + 1
            break

    return {
        "actions_count": dist,
        "actions_freq": freqs,
        "action_entropy": entropy,
        "steps_taken": int(len(episode.actions)),
        "steps_to_goal": steps_to_goal,
        "final_position": positions[-1] if positions else None,
        "position_mean": float(np.mean(positions)) if positions else None,
        "position_std": float(np.std(positions)) if positions else None,
        "peak_reward": float(np.max(rewards)) if rewards.size else 0.0,
        "avg_reward": float(np.mean(rewards)) if rewards.size else 0.0,
        "total_reward": float(np.sum(rewards)) if rewards.size else 0.0,
    }


def perturb_pattern_state(pattern_state: dict, noise_std: float, rng: np.random.Generator) -> dict:
    """Apply Gaussian noise to internal_state and W to model transfer distortion."""
    if noise_std <= 0:
        return {
            "internal_state": np.asarray(pattern_state["internal_state"], dtype=np.float64).copy(),
            "W": np.asarray(pattern_state["W"], dtype=np.float64).copy(),
        }
    internal = np.asarray(pattern_state["internal_state"], dtype=np.float64)
    W = np.asarray(pattern_state["W"], dtype=np.float64)
    noisy_internal = internal + rng.normal(0.0, noise_std, size=internal.shape)
    noisy_W = W + rng.normal(0.0, noise_std, size=W.shape)
    return {"internal_state": noisy_internal, "W": noisy_W}


def run_episode_with_snapshot(
    env: GridWorldEnv,
    agent: PatternAgent,
    max_steps: int,
    snapshot_step: int | None,
) -> tuple[EpisodeResult, dict]:
    obs = env.reset()
    obs_history: list[np.ndarray] = []
    actions: list[int] = []
    rewards: list[float] = []
    snapshot_state: dict | None = None

    for t in range(max_steps):
        obs_history.append(obs.copy())
        action = agent.policy(obs)
        obs, reward, done, _ = env.step(action)
        actions.append(int(action))
        rewards.append(float(reward))

        if snapshot_step is not None and t == snapshot_step:
            snapshot_state = agent.get_pattern_state()

        if done:
            break

    if snapshot_state is None:
        snapshot_state = agent.get_pattern_state()

    episode = EpisodeResult(
        observations=np.array(obs_history, dtype=np.float64),
        actions=actions,
        rewards=rewards,
    )
    return episode, snapshot_state


def run_episode(env: GridWorldEnv, agent: PatternAgent, max_steps: int) -> EpisodeResult:
    return run_episode_with_snapshot(env, agent, max_steps, snapshot_step=None)[0]


def snapshot_run(
    env: GridWorldEnv, agent: PatternAgent, snapshot_step: int
) -> tuple[EpisodeResult, dict, dict]:
    """Run a single episode, capturing pattern state at `snapshot_step` and the final state."""
    episode, snapshot_state = run_episode_with_snapshot(
        env, agent, env.max_steps, snapshot_step=snapshot_step
    )
    final_state = agent.get_pattern_state()
    return episode, snapshot_state, final_state


def evaluate_copy_divergence(
    mid_pattern_state: dict,
    observations: np.ndarray,
    window: int,
    temperature: float,
    state_momentum: float,
    weight_scale: float,
    noise_std: float = 0.0,
    rng: np.random.Generator | None = None,
) -> tuple[float, list[int], list[int]]:
    if observations.size == 0:
        return 0.0, [], []

    window = min(window, len(observations))
    test_obs = observations[:window]

    rng = rng or np.random.default_rng()
    perturbed_state = perturb_pattern_state(mid_pattern_state, noise_std=noise_std, rng=rng)

    copy_1 = PatternAgent.from_pattern_state(
        perturbed_state,
        temperature=temperature,
        state_momentum=state_momentum,
        weight_scale=weight_scale,
    )
    copy_2 = PatternAgent.from_pattern_state(
        perturbed_state,
        temperature=temperature,
        state_momentum=state_momentum,
        weight_scale=weight_scale,
    )

    actions_1: list[int] = []
    actions_2: list[int] = []
    for obs in test_obs:
        actions_1.append(copy_1.policy(obs))
        actions_2.append(copy_2.policy(obs))

    divergence = behavior_divergence(actions_1, actions_2)
    return divergence, actions_1, actions_2


def serialize_pattern_state(pattern_state: dict) -> dict:
    return {
        "internal_state": np.asarray(pattern_state["internal_state"], dtype=np.float64).tolist(),
        "W": np.asarray(pattern_state["W"], dtype=np.float64).tolist(),
    }


def save_run_log(payload: dict, log_dir: Path = LOG_DIR) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    run_id = payload.get("run_id", stamp)
    path = log_dir / f"{run_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def build_payload(
    run_id: str,
    env: GridWorldEnv,
    agent: PatternAgent,
    episode: EpisodeResult,
    mid_pattern_state: dict,
    final_pattern_state: dict,
    copy_actions_1: Sequence[int],
    copy_actions_2: Sequence[int],
    continuity_score: float,
    behavior_score: float,
    snapshot_step: int,
    episode_summary: dict,
    transfer_tests: list[dict],
    continuity_threshold: float,
) -> dict:
    episode_total_reward = float(np.sum(episode.rewards))
    goal_reached = bool(any(r > 0.0 for r in episode.rewards))

    below_threshold = [
        test for test in transfer_tests if test["continuity_vs_mid"] < continuity_threshold
    ]
    first_drop = below_threshold[0] if below_threshold else None

    return {
        "schema_version": "1.1",
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "env": {
                "size": env.size,
                "max_steps": env.max_steps,
                "seed": env.seed,
            },
            "agent": {
                "obs_dim": agent.obs_dim,
                "internal_dim": agent.internal_dim,
                "temperature": agent.temperature,
                "state_momentum": agent.state_momentum,
                "weight_scale": agent.weight_scale,
                "seed": agent.seed,
            },
            "snapshot_step": snapshot_step,
            "copy_eval_window": len(copy_actions_1),
            "continuity_threshold": continuity_threshold,
            "transfer_noise_grid": transfer_tests and [t["noise_std"] for t in transfer_tests] or [],
        },
        "metrics": {
            "continuity_mid_to_final": continuity_score,
            "behavior_divergence_mid_copies": behavior_score,
            "behavior_alignment_mid_copies": 1.0 - behavior_score,
            "episode_total_reward": episode_total_reward,
            "goal_reached": goal_reached,
            "continuity_gap_from_one": 1.0 - continuity_score,
        },
        "episode": {
            "length": episode.length,
            **episode.to_log(),
        },
        "episode_summary": episode_summary,
        "transfer_tests": transfer_tests,
        "transfer_threshold_crossing": first_drop,
        "pattern_state": {
            "mid": serialize_pattern_state(mid_pattern_state),
            "final": serialize_pattern_state(final_pattern_state),
        },
        "copy_actions": {
            "copy_1": list(copy_actions_1),
            "copy_2": list(copy_actions_2),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the QMPT Lab copy-vs-transfer experiment with structured logging.",
    )
    parser.add_argument("--size", type=int, default=10, help="Grid size.")
    parser.add_argument("--max-steps", type=int, default=50, help="Maximum steps per episode.")
    parser.add_argument("--mid-step", type=int, default=20, help="Step to snapshot pattern state.")
    parser.add_argument("--internal-dim", type=int, default=16, help="Internal state dimension.")
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Softmax temperature for the policy.",
    )
    parser.add_argument(
        "--state-momentum",
        type=float,
        default=0.9,
        help="Decay applied when updating internal state.",
    )
    parser.add_argument(
        "--weight-scale",
        type=float,
        default=0.1,
        help="Weight initialization scale before normalization.",
    )
    parser.add_argument("--seed-env", type=int, default=42, help="Environment RNG seed.")
    parser.add_argument("--seed-agent", type=int, default=123, help="Agent RNG seed.")
    parser.add_argument(
        "--seed-transfer-noise",
        type=int,
        default=None,
        help="Seed for transfer noise sampling; None = random.",
    )
    parser.add_argument(
        "--copy-eval-window",
        type=int,
        default=30,
        help="Number of observations used to compare two copies.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=LOG_DIR,
        help="Directory to store structured logs.",
    )
    parser.add_argument(
        "--transfer-noise-grid",
        type=str,
        default="0.0",
        help="Comma-separated noise std levels applied to pattern transfer (W and internal_state).",
    )
    parser.add_argument(
        "--continuity-threshold",
        type=float,
        default=0.95,
        help="Threshold to flag when continuity vs. mid drops under transfer noise.",
    )
    return parser.parse_args()


def run_experiment(
    *,
    size: int = 10,
    max_steps: int = 50,
    mid_step: int = 20,
    internal_dim: int = 16,
    temperature: float = 1.0,
    state_momentum: float = 0.9,
    weight_scale: float = 0.1,
    seed_env: int | None = 42,
    seed_agent: int | None = 123,
    copy_eval_window: int = 30,
    log_dir: Path | None = None,
    run_id: str | None = None,
    transfer_noise_grid: Sequence[float] | None = None,
    seed_transfer_noise: int | None = None,
    continuity_threshold: float = 0.95,
) -> tuple[str, Path, dict]:
    """Programmatic entrypoint to run a single experiment and save the log."""
    log_dir = log_dir or LOG_DIR
    env = GridWorldEnv(size=size, max_steps=max_steps, seed=seed_env)
    agent = PatternAgent(
        obs_dim=env.obs_dim,
        internal_dim=internal_dim,
        seed=seed_agent,
        temperature=temperature,
        state_momentum=state_momentum,
        weight_scale=weight_scale,
    )

    snapshot_step = max(0, min(mid_step, max_steps - 1))
    episode, mid_pattern_state, final_pattern_state = snapshot_run(
        env, agent, snapshot_step=snapshot_step
    )
    episode_summary = summarize_episode(episode, env_size=env.size)

    continuity_score = continuity_cosine(mid_pattern_state, final_pattern_state)
    behavior_score, copy_actions_1, copy_actions_2 = evaluate_copy_divergence(
        mid_pattern_state=mid_pattern_state,
        observations=episode.observations,
        window=copy_eval_window,
        temperature=temperature,
        state_momentum=state_momentum,
        weight_scale=weight_scale,
    )

    # Evaluate transfer distortions over a grid of noise levels.
    noise_levels = list(transfer_noise_grid) if transfer_noise_grid else [0.0]
    noise_rng = np.random.default_rng(seed_transfer_noise)
    transfer_tests: list[dict] = []
    for noise_std in noise_levels:
        noisy_state = perturb_pattern_state(mid_pattern_state, noise_std=noise_std, rng=noise_rng)
        continuity_vs_mid = continuity_cosine(mid_pattern_state, noisy_state)
        divergence_noise, actions_1_n, actions_2_n = evaluate_copy_divergence(
            mid_pattern_state=noisy_state,
            observations=episode.observations,
            window=copy_eval_window,
            temperature=temperature,
            state_momentum=state_momentum,
            weight_scale=weight_scale,
        )
        transfer_tests.append(
            {
                "noise_std": float(noise_std),
                "continuity_vs_mid": continuity_vs_mid,
                "behavior_divergence": divergence_noise,
                "behavior_alignment": 1.0 - divergence_noise,
                "actions_1_sample": actions_1_n[:5],
                "actions_2_sample": actions_2_n[:5],
            }
        )

    resolved_run_id = run_id or datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%S%fZ")
    payload = build_payload(
        run_id=resolved_run_id,
        env=env,
        agent=agent,
        episode=episode,
        mid_pattern_state=mid_pattern_state,
        final_pattern_state=final_pattern_state,
        copy_actions_1=copy_actions_1,
        copy_actions_2=copy_actions_2,
        continuity_score=continuity_score,
        behavior_score=behavior_score,
        snapshot_step=snapshot_step,
        episode_summary=episode_summary,
        transfer_tests=transfer_tests,
        continuity_threshold=continuity_threshold,
    )
    log_path = save_run_log(payload, log_dir=log_dir)

    return resolved_run_id, log_path, payload


def main():
    args = parse_args()
    run_id, log_path, payload = run_experiment(
        size=args.size,
        max_steps=args.max_steps,
        mid_step=args.mid_step,
        internal_dim=args.internal_dim,
        temperature=args.temperature,
        state_momentum=args.state_momentum,
        weight_scale=args.weight_scale,
        seed_env=args.seed_env,
        seed_agent=args.seed_agent,
        copy_eval_window=args.copy_eval_window,
        log_dir=args.log_dir,
        transfer_noise_grid=[float(x) for x in args.transfer_noise_grid.split(",") if x != ""],
        seed_transfer_noise=args.seed_transfer_noise,
        continuity_threshold=args.continuity_threshold,
    )

    metrics = payload["metrics"]
    snapshot_step = payload["config"]["snapshot_step"]
    episode_length = payload["episode"]["length"]
    transfer_tests = payload.get("transfer_tests", [])
    crossing = payload.get("transfer_threshold_crossing")

    print("=== QMPT Lab: copy vs transfer experiment ===")
    print(f"Run ID = {run_id}")
    print(f"Snapshot step (0-indexed) = {snapshot_step}")
    print(f"Continuity C(Psi_mid, Psi_final) = {metrics['continuity_mid_to_final']:.6f}")
    print(
        "Behavioral divergence of two mid-state copies = "
        f"{metrics['behavior_divergence_mid_copies']:.6f}"
    )
    if transfer_tests:
        best = max(transfer_tests, key=lambda r: r["continuity_vs_mid"])
        worst = min(transfer_tests, key=lambda r: r["continuity_vs_mid"])
        print(
            f"Transfer noise sweep: best continuity {best['continuity_vs_mid']:.4f} "
            f"at noise {best['noise_std']}, worst {worst['continuity_vs_mid']:.4f} "
            f"at noise {worst['noise_std']}"
        )
        if crossing:
            print(
                f"Continuity crossed below threshold ({payload['config']['continuity_threshold']}) "
                f"at noise {crossing['noise_std']} (C={crossing['continuity_vs_mid']:.4f})"
            )
    print(f"Episode length = {episode_length} steps")
    print(f"Structured log saved to: {log_path}")


if __name__ == "__main__":
    main()
