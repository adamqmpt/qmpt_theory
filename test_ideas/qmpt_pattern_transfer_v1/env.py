from __future__ import annotations

import numpy as np


class GridWorldEnv:
    """Simple 1D grid environment as a layer L."""

    ACTIONS = (-1, 0, 1)

    def __init__(self, size: int = 10, max_steps: int = 50, seed: int | None = None):
        if size <= 1:
            raise ValueError("size must be > 1")
        self.size = int(size)
        self.max_steps = int(max_steps)
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.t = 0
        self.pos = 0

    @property
    def obs_dim(self) -> int:
        return self.size + 1  # one-hot position + normalized time

    def reset(self) -> np.ndarray:
        self.pos = int(self.rng.integers(0, self.size))
        self.t = 0
        return self._get_obs()

    def step(self, action: int):
        if action not in self.ACTIONS:
            raise ValueError(f"Action must be one of {self.ACTIONS}")
        self.pos = int(np.clip(self.pos + action, 0, self.size - 1))
        self.t += 1
        obs = self._get_obs()
        reward = 1.0 if self.pos == self.size - 1 else 0.0
        done = self.t >= self.max_steps
        info = {"pos": self.pos, "t": self.t}
        return obs, reward, done, info

    def _get_obs(self) -> np.ndarray:
        pos_vec = np.zeros(self.size, dtype=np.float32)
        pos_vec[self.pos] = 1.0
        t_norm = np.array([self.t / max(self.max_steps, 1)], dtype=np.float32)
        return np.concatenate([pos_vec, t_norm])

