from __future__ import annotations

import numpy as np

try:  # pragma: no cover
    from .metrics import behavior_divergence, continuity_cosine, awareness_summary
except ImportError:  # pragma: no cover
    from metrics import behavior_divergence, continuity_cosine, awareness_summary


def run_episode(env, agent, max_steps: int):
    obs = env.reset()
    obs_history = []
    actions = []
    rewards = []
    awareness_ts = []
    pattern_mid = None
    mid_step = max_steps // 2

    for t in range(max_steps):
        obs_history.append(obs.copy())
        action = agent.policy(obs)
        actions.append(action)
        obs, reward, done, info = env.step(action)
        rewards.append(float(reward))
        awareness_ts.extend(agent.awareness_values[-1:])
        if t == mid_step:
            pattern_mid = agent.get_pattern_state()
        if done:
            break

    if pattern_mid is None:
        pattern_mid = agent.get_pattern_state()
    pattern_final = agent.get_pattern_state()

    return {
        "observations": np.array(obs_history, dtype=np.float32),
        "actions": actions,
        "rewards": rewards,
        "awareness": awareness_ts,
        "pattern_mid": pattern_mid,
        "pattern_final": pattern_final,
        "mid_step": mid_step,
    }


def copy_experiment(obs_sequence: np.ndarray, pattern_state_mid: dict, agent_cls, horizon: int):
    agent_a = agent_cls.from_pattern_state(pattern_state_mid)
    agent_b = agent_cls.from_pattern_state(pattern_state_mid)
    actions_a = []
    actions_b = []
    # consume up to horizon observations
    for obs in obs_sequence[:horizon]:
        actions_a.append(agent_a.policy(obs))
        actions_b.append(agent_b.policy(obs))
    divergence = behavior_divergence(actions_a, actions_b)
    return {
        "copy_divergence": divergence,
        "actions_a": actions_a,
        "actions_b": actions_b,
    }


def transfer_experiment(env_factory, pattern_state_mid: dict, agent_cls, horizon: int):
    env = env_factory()
    obs = env.reset()
    transferred_agent = agent_cls.from_pattern_state(pattern_state_mid)
    baseline_agent = agent_cls.from_pattern_state(pattern_state_mid)
    actions_trans = []
    actions_base = []
    awareness_trans = []
    pattern_after = None

    for _ in range(horizon):
        act_t = transferred_agent.policy(obs)
        act_b = baseline_agent.policy(obs)
        actions_trans.append(act_t)
        actions_base.append(act_b)
        obs, _, done, _ = env.step(act_t)
        awareness_trans.extend(transferred_agent.awareness_values[-1:])
        if done:
            break
    pattern_after = transferred_agent.get_pattern_state()
    cont_mid_to_trans = continuity_cosine(pattern_state_mid, pattern_after)
    div_transfer = behavior_divergence(actions_trans, actions_base)
    return {
        "continuity_mid_to_transferred": cont_mid_to_trans,
        "behavior_divergence_transfer_vs_baseline": div_transfer,
        "awareness_after": awareness_summary(awareness_trans),
        "actions_trans": actions_trans,
        "actions_base": actions_base,
    }
