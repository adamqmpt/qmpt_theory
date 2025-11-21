from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass
class AgentConfig:
    obs_dim: int
    internal_dim: int = 128
    self_model_dim: int = 64
    hidden_dim: int = 256
    action_dim: int = 5  # stay, up, down, left, right
    weight_scale: float = 0.1
    seed: int | None = None
    policy_temperature: float = 1.0
    self_model_lr: float = 0.05
    transfer_noise_std: float = 0.0


class PatternAgentAdv:
    """
    Pattern agent with internal state, self-model, and MLP policy.
    """

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)

        scale = cfg.weight_scale / np.sqrt(cfg.obs_dim + cfg.internal_dim + cfg.self_model_dim)
        self.internal_state = self.rng.normal(0.0, scale, size=(cfg.internal_dim,)).astype(np.float32)
        self.self_model_state = self.rng.normal(0.0, scale, size=(cfg.self_model_dim,)).astype(np.float32)

        # Policy network
        self.Wp1 = self.rng.normal(0.0, scale, size=(cfg.hidden_dim, cfg.obs_dim + cfg.internal_dim + cfg.self_model_dim)).astype(np.float32)
        self.bp1 = np.zeros((cfg.hidden_dim,), dtype=np.float32)
        self.Wp2 = self.rng.normal(0.0, scale, size=(cfg.action_dim, cfg.hidden_dim)).astype(np.float32)
        self.bp2 = np.zeros((cfg.action_dim,), dtype=np.float32)

        # Self-model update network (small MLP)
        sm_in = cfg.obs_dim + cfg.internal_dim + 2  # + action + reward
        self.Ws1 = self.rng.normal(0.0, scale, size=(cfg.self_model_dim, sm_in)).astype(np.float32)
        self.bs1 = np.zeros((cfg.self_model_dim,), dtype=np.float32)
        self.Ws2 = self.rng.normal(0.0, scale, size=(cfg.self_model_dim, cfg.self_model_dim)).astype(np.float32)
        self.bs2 = np.zeros((cfg.self_model_dim,), dtype=np.float32)

        self.last_action = 0.0
        self.last_reward = 0.0

    def policy(self, obs: np.ndarray) -> int:
        x = np.concatenate([obs.astype(np.float32), self.internal_state, self.self_model_state])
        h = np.tanh(self.Wp1 @ x + self.bp1)
        logits = (self.Wp2 @ h + self.bp2) / max(self.cfg.policy_temperature, 1e-6)
        probs = self._softmax(logits)
        act = int(self.rng.choice(self.cfg.action_dim, p=probs))

        # update internal/self-model
        self._update_internal(h)
        self._update_self_model(obs, act, self.last_reward)
        self.last_action = float(act)
        return act

    def get_pattern_state(self) -> Dict[str, np.ndarray]:
        return {
            "internal_state": self.internal_state.copy(),
            "self_model_state": self.self_model_state.copy(),
            "Wp1": self.Wp1.copy(),
            "bp1": self.bp1.copy(),
            "Wp2": self.Wp2.copy(),
            "bp2": self.bp2.copy(),
            "Ws1": self.Ws1.copy(),
            "bs1": self.bs1.copy(),
            "Ws2": self.Ws2.copy(),
            "bs2": self.bs2.copy(),
        }

    @classmethod
    def from_pattern_state(cls, cfg: AgentConfig, pattern_state: Dict[str, np.ndarray], transfer_noise_std: float = 0.0):
        agent = cls(cfg)
        rng = np.random.default_rng(cfg.seed)

        def inject_noise(arr: np.ndarray):
            if transfer_noise_std <= 0:
                return arr.copy()
            return arr + rng.normal(0.0, transfer_noise_std, size=arr.shape)

        agent.internal_state = inject_noise(np.asarray(pattern_state["internal_state"], dtype=np.float32))
        agent.self_model_state = inject_noise(np.asarray(pattern_state["self_model_state"], dtype=np.float32))
        agent.Wp1 = inject_noise(np.asarray(pattern_state["Wp1"], dtype=np.float32))
        agent.bp1 = inject_noise(np.asarray(pattern_state["bp1"], dtype=np.float32))
        agent.Wp2 = inject_noise(np.asarray(pattern_state["Wp2"], dtype=np.float32))
        agent.bp2 = inject_noise(np.asarray(pattern_state["bp2"], dtype=np.float32))
        agent.Ws1 = inject_noise(np.asarray(pattern_state["Ws1"], dtype=np.float32))
        agent.bs1 = inject_noise(np.asarray(pattern_state["bs1"], dtype=np.float32))
        agent.Ws2 = inject_noise(np.asarray(pattern_state["Ws2"], dtype=np.float32))
        agent.bs2 = inject_noise(np.asarray(pattern_state["bs2"], dtype=np.float32))
        return agent

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        logits = logits - np.max(logits)
        exps = np.exp(logits)
        probs = exps / np.sum(exps)
        return probs

    def _update_internal(self, h: np.ndarray):
        projected = h[: self.cfg.internal_dim]
        self.internal_state = np.tanh(0.9 * self.internal_state + 0.1 * projected)

    def _update_self_model(self, obs: np.ndarray, action: int, reward: float):
        obs_vec = obs.astype(np.float32)
        sm_in = np.concatenate(
            [
                obs_vec,
                self.internal_state,
                np.array([float(action), float(reward)], dtype=np.float32),
            ]
        )
        sm_hidden = np.tanh(self.Ws1 @ sm_in + self.bs1)
        sm_delta = np.tanh(self.Ws2 @ sm_hidden + self.bs2)
        self.self_model_state = (1 - self.cfg.self_model_lr) * self.self_model_state + self.cfg.self_model_lr * sm_delta
