from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from numpy.typing import NDArray


Action = int


@dataclass
class GridWorldConfig:
    """Configuration for the 1D grid environment."""

    size: int = 10
    max_steps: int = 100
    seed: int | None = None


class GridWorldEnv:
    """
    Minimal 1D grid used as layer L:
    - a line of `size` cells;
    - the agent moves left, right, or stays still;
    - reward is granted only when the agent reaches the right edge.
    """

    ACTIONS: Tuple[Action, ...] = (-1, 0, 1)

    def __init__(self, size: int = 10, max_steps: int = 100, seed: int | None = None):
        if size <= 0:
            raise ValueError("`size` must be positive.")
        if max_steps <= 0:
            raise ValueError("`max_steps` must be positive.")

        self.size = int(size)
        self.max_steps = int(max_steps)
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.t = 0
        self.pos = 0
        self._last_action: Action | None = None

    @property
    def obs_dim(self) -> int:
        """Observation dimension: one-hot position plus normalized time."""
        return self.size + 1

    def reset(self) -> NDArray[np.float64]:
        """Reset environment to a random position and return the first observation."""
        self.pos = int(self.rng.integers(0, self.size))
        self.t = 0
        self._last_action = None
        return self._get_obs()

    def _get_obs(self) -> NDArray[np.float64]:
        pos_vec = np.zeros(self.size, dtype=np.float64)
        pos_vec[self.pos] = 1.0
        t_norm = np.array([self.t / float(self.max_steps)], dtype=np.float64)
        return np.concatenate([pos_vec, t_norm])

    def step(self, action: Action):
        """Apply action {-1, 0, 1} and return (obs, reward, done, info)."""
        if action not in self.ACTIONS:
            raise ValueError(f"Action must be one of {self.ACTIONS}, got {action}.")

        self.pos = int(np.clip(self.pos + action, 0, self.size - 1))
        self.t += 1
        self._last_action = action

        obs = self._get_obs()
        reward = 1.0 if self.pos == self.size - 1 else 0.0
        done = self.t >= self.max_steps or self.pos == self.size - 1
        info = {
            "position": self.pos,
            "time_step": self.t,
            "last_action": action,
            "reached_goal": self.pos == self.size - 1,
        }

        return obs, float(reward), done, info
