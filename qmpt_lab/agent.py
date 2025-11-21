from __future__ import annotations

from typing import Tuple

import numpy as np
from numpy.typing import NDArray


class PatternAgent:
    """
    Simple pattern policy (Psi) with internal state:
    - `internal_state` acts as memory/self-model seed;
    - `W` are linear policy parameters mapping [obs, internal] -> logits over 3 actions.
    """

    ACTIONS: Tuple[int, ...] = (-1, 0, 1)

    def __init__(
        self,
        obs_dim: int,
        internal_dim: int = 16,
        seed: int | None = None,
        temperature: float = 1.0,
        state_momentum: float = 0.9,
        weight_scale: float = 0.1,
    ):
        if obs_dim <= 0:
            raise ValueError("`obs_dim` must be positive.")
        if internal_dim <= 0:
            raise ValueError("`internal_dim` must be positive.")
        if not 0.0 < state_momentum < 1.0:
            raise ValueError("`state_momentum` must be in (0, 1).")

        self.obs_dim = int(obs_dim)
        self.internal_dim = int(internal_dim)
        self.temperature = max(float(temperature), 1e-6)
        self.state_momentum = float(state_momentum)
        self.weight_scale = float(weight_scale)

        self.seed = seed
        self.rng = np.random.default_rng(seed)

        scale = self.weight_scale / np.sqrt(self.obs_dim + self.internal_dim)
        self.internal_state = self.rng.normal(0.0, scale, size=(self.internal_dim,)).astype(
            np.float64
        )
        self.W = self.rng.normal(
            0.0, scale, size=(len(self.ACTIONS), self.obs_dim + self.internal_dim)
        ).astype(np.float64)

    def policy(self, obs: NDArray[np.float64]) -> int:
        """Return action in {-1, 0, 1} sampled from the policy."""
        obs_vec = np.asarray(obs, dtype=np.float64)
        if obs_vec.shape[0] != self.obs_dim:
            raise ValueError(f"Expected obs_dim {self.obs_dim}, got {obs_vec.shape[0]}.")

        x = np.concatenate([obs_vec, self.internal_state])
        logits = self.W @ x
        probs = self._softmax(logits / self.temperature)

        idx = int(self.rng.choice(len(self.ACTIONS), p=probs))
        action = self.ACTIONS[idx]

        tail = x[-self.internal_dim :]
        updated_state = self.state_momentum * self.internal_state + (1.0 - self.state_momentum) * tail
        self.internal_state = np.tanh(updated_state)

        return action

    def get_pattern_state(self) -> dict:
        """Return a snapshot of the pattern state Psi(t)."""
        return {
            "internal_state": self.internal_state.copy(),
            "W": self.W.copy(),
        }

    @classmethod
    def from_pattern_state(
        cls,
        pattern_state: dict,
        temperature: float = 1.0,
        state_momentum: float = 0.9,
        weight_scale: float = 0.1,
    ):
        """
        Restore Psi from a saved state.
        Model of transferring the pattern to a fresh carrier.
        """
        W = np.asarray(pattern_state["W"], dtype=np.float64)
        internal = np.asarray(pattern_state["internal_state"], dtype=np.float64)

        internal_dim = internal.shape[0]
        obs_dim_plus_internal = W.shape[1]
        obs_dim = obs_dim_plus_internal - internal_dim
        if obs_dim <= 0:
            raise ValueError("Invalid pattern state: obs_dim must be positive.")

        agent = cls(
            obs_dim=obs_dim,
            internal_dim=internal_dim,
            temperature=temperature,
            state_momentum=state_momentum,
            weight_scale=weight_scale,
        )
        agent.W = W.copy()
        agent.internal_state = internal.copy()
        return agent

    @staticmethod
    def _softmax(logits: NDArray[np.float64]) -> NDArray[np.float64]:
        """Numerically stable softmax."""
        logits = np.asarray(logits, dtype=np.float64)
        max_logit = np.max(logits)
        exp_shifted = np.exp(logits - max_logit)
        probs = exp_shifted / np.maximum(np.sum(exp_shifted), 1e-12)
        # Normalize one more time to guard against round-off.
        return probs / np.sum(probs)
