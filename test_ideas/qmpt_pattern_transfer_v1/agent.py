from __future__ import annotations

import numpy as np


class PatternAgent:
    """Pattern Ψ with internal state, self-model, and simple policy."""

    ACTIONS = (-1, 0, 1)

    def __init__(self, obs_dim: int, internal_dim: int = 16, self_model_dim: int = 8, seed: int | None = None):
        self.obs_dim = obs_dim
        self.internal_dim = internal_dim
        self.self_model_dim = self_model_dim
        self.rng = np.random.default_rng(seed)
        scale = 0.1 / np.sqrt(obs_dim + internal_dim + self_model_dim)
        self.internal_state = self.rng.normal(0.0, scale, size=(internal_dim,)).astype(np.float32)
        self.self_model_state = self.rng.normal(0.0, scale, size=(self_model_dim,)).astype(np.float32)
        self.W = self.rng.normal(0.0, scale, size=(3, obs_dim + internal_dim + self_model_dim)).astype(np.float32)
        # self-model predictor for next internal state
        self.W_sm = self.rng.normal(0.0, scale, size=(internal_dim, internal_dim)).astype(np.float32)
        self.awareness_values: list[float] = []

    def policy(self, obs: np.ndarray) -> int:
        obs_vec = np.asarray(obs, dtype=np.float32)
        x = np.concatenate([obs_vec, self.internal_state, self.self_model_state])
        logits = self.W @ x
        probs = self._softmax(logits)
        idx = int(self.rng.choice(3, p=probs))
        action = self.ACTIONS[idx]

        # predict next internal state and update awareness
        predicted = self.W_sm @ self.internal_state
        obs_pad = np.zeros_like(self.internal_state)
        obs_slice = obs_vec[: min(self.internal_dim, obs_vec.shape[0])]
        obs_pad[: obs_slice.shape[0]] = obs_slice
        self.internal_state = 0.9 * self.internal_state + 0.1 * obs_pad
        error = float(np.linalg.norm(predicted - self.internal_state))
        norm = max(np.linalg.norm(self.internal_state) + 1e-6, 1.0)
        awareness = max(0.0, 1.0 - error / norm)
        self.awareness_values.append(awareness)

        # simple self-model drift
        self.self_model_state = 0.95 * self.self_model_state + 0.05 * predicted[: self.self_model_dim]
        return action

    def get_pattern_state(self) -> dict:
        return {
            "internal_state": self.internal_state.copy(),
            "self_model_state": self.self_model_state.copy(),
            "W": self.W.copy(),
            "W_sm": self.W_sm.copy(),
            "awareness_mean": float(np.mean(self.awareness_values)) if self.awareness_values else 0.0,
        }

    @classmethod
    def from_pattern_state(cls, pattern_state: dict):
        internal = pattern_state["internal_state"]
        internal_dim = internal.shape[0]
        self_model_dim = pattern_state["self_model_state"].shape[0]
        W = pattern_state["W"]
        obs_dim = W.shape[1] - internal_dim - self_model_dim
        agent = cls(obs_dim=obs_dim, internal_dim=internal_dim, self_model_dim=self_model_dim)
        agent.internal_state = internal.copy()
        agent.self_model_state = pattern_state["self_model_state"].copy()
        agent.W = W.copy()
        agent.W_sm = pattern_state["W_sm"].copy()
        return agent

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        logits = logits - np.max(logits)
        exps = np.exp(logits)
        return exps / np.sum(exps)
