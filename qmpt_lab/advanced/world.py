from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

Action = int


@dataclass
class WorldConfig:
    width: int = 32
    height: int = 32
    n_layers: int = 2
    n_agents: int = 8
    obstacle_ratio: float = 0.1
    resource_ratio: float = 0.05
    view_radius: int = 3  # 7x7 window by default
    respawn_prob: float = 0.01
    portal_ratio: float = 0.02
    seed: int | None = None
    diffusion: float = 0.0  # optional cognitive diffusion


class MultiLayerWorld:
    """
    Simple 2D multi-layer gridworld with physical and cognitive layers.
    Physical layer tracks obstacles/resources/portals; cognitive layer tracks signals and agent influences.
    """

    def __init__(self, config: WorldConfig):
        self.cfg = config
        self.rng = np.random.default_rng(config.seed)
        self.t = 0
        self.agent_positions: Dict[int, Tuple[int, int]] = {}
        self.resources = np.zeros((self.cfg.height, self.cfg.width), dtype=np.int8)
        self.obstacles = np.zeros_like(self.resources)
        self.portals = np.zeros_like(self.resources)
        self.cognitive_map = np.zeros((self.cfg.height, self.cfg.width), dtype=np.float32)
        self.reset(config.seed)

    def reset(self, seed: int | None = None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.t = 0
        h, w = self.cfg.height, self.cfg.width
        self.obstacles = (self.rng.random((h, w)) < self.cfg.obstacle_ratio).astype(np.int8)
        self.resources = (self.rng.random((h, w)) < self.cfg.resource_ratio).astype(np.int8)
        self.portals = (self.rng.random((h, w)) < self.cfg.portal_ratio).astype(np.int8)
        self.cognitive_map = np.zeros((h, w), dtype=np.float32)
        self.agent_positions = {}

        for agent_id in range(self.cfg.n_agents):
            self.agent_positions[agent_id] = self._sample_free_cell()

        return self._build_observations()

    def _sample_free_cell(self) -> Tuple[int, int]:
        h, w = self.cfg.height, self.cfg.width
        while True:
            y = int(self.rng.integers(0, h))
            x = int(self.rng.integers(0, w))
            if self.obstacles[y, x] == 0:
                return y, x

    def step(self, actions: Dict[int, Action]):
        rewards = {}
        info = {"anomaly_score": 0.0}

        # Move agents
        for agent_id, action in actions.items():
            y, x = self.agent_positions.get(agent_id, (0, 0))
            ny, nx = self._next_pos(y, x, action)
            if self.obstacles[ny, nx] == 1:
                ny, nx = y, x  # blocked
            self.agent_positions[agent_id] = (ny, nx)

        # Collect resources and portals effects
        total_resources_before = int(self.resources.sum())
        for agent_id, (y, x) in self.agent_positions.items():
            reward = 0.0
            if self.resources[y, x] == 1:
                reward += 1.0
                self.resources[y, x] = 0
            if self.portals[y, x] == 1:
                reward += 0.5
                # simple portal: random teleport
                self.agent_positions[agent_id] = self._sample_free_cell()
            rewards[agent_id] = reward

        # Cognitive layer update: increment visited cells, diffuse map
        for agent_id, (y, x) in self.agent_positions.items():
            self.cognitive_map[y, x] += 0.2
        self.cognitive_map *= 0.97  # decay
        if self.cfg.diffusion > 0.0:
            self.cognitive_map = self._diffuse(self.cognitive_map, self.cfg.diffusion)

        # Respawn resources
        respawn_mask = self.rng.random(self.resources.shape) < self.cfg.respawn_prob
        self.resources = np.clip(self.resources + respawn_mask.astype(np.int8), 0, 1)

        total_resources_after = int(self.resources.sum())
        anomaly_score = abs(total_resources_after - total_resources_before) / max(
            1, self.cfg.width * self.cfg.height
        )
        info["anomaly_score"] = anomaly_score

        self.t += 1
        done = False  # episodes handled by runner
        return self._build_observations(), rewards, done, info

    def _next_pos(self, y: int, x: int, action: Action) -> Tuple[int, int]:
        # actions: 0 stay, 1 up, 2 down, 3 left, 4 right
        if action == 1:
            y = max(0, y - 1)
        elif action == 2:
            y = min(self.cfg.height - 1, y + 1)
        elif action == 3:
            x = max(0, x - 1)
        elif action == 4:
            x = min(self.cfg.width - 1, x + 1)
        return y, x

    def _local_view(self, y: int, x: int) -> np.ndarray:
        r = self.cfg.view_radius
        y0, y1 = max(0, y - r), min(self.cfg.height, y + r + 1)
        x0, x1 = max(0, x - r), min(self.cfg.width, x + r + 1)

        view_res = np.zeros((2 * r + 1, 2 * r + 1), dtype=np.float32)
        view_obs = np.zeros_like(view_res)
        view_portal = np.zeros_like(view_res)
        view_cog = np.zeros_like(view_res)

        sub_res = self.resources[y0:y1, x0:x1]
        sub_obs = self.obstacles[y0:y1, x0:x1]
        sub_portal = self.portals[y0:y1, x0:x1]
        sub_cog = self.cognitive_map[y0:y1, x0:x1]
        view_res[: sub_res.shape[0], : sub_res.shape[1]] = sub_res
        view_obs[: sub_obs.shape[0], : sub_obs.shape[1]] = sub_obs
        view_portal[: sub_portal.shape[0], : sub_portal.shape[1]] = sub_portal
        view_cog[: sub_cog.shape[0], : sub_cog.shape[1]] = sub_cog

        return np.stack([view_res, view_obs, view_portal, view_cog], axis=0).reshape(-1)

    def _build_observations(self) -> Dict[int, np.ndarray]:
        observations: Dict[int, np.ndarray] = {}
        r = self.cfg.view_radius
        view_size = (2 * r + 1) * (2 * r + 1) * 4
        layer_encoding = np.eye(self.cfg.n_layers, dtype=np.float32)[0]  # assume physical layer focus
        global_signal = np.array(
            [
                self.resources.mean(),
                self.cognitive_map.mean(),
                float(self.t),
            ],
            dtype=np.float32,
        )
        for agent_id, (y, x) in self.agent_positions.items():
            local = self._local_view(y, x)
            neighbors = self._neighbor_count(y, x)
            obs = np.concatenate([local, layer_encoding, global_signal, np.array([neighbors], dtype=np.float32)])
            observations[agent_id] = obs
        return observations

    def _neighbor_count(self, y: int, x: int, radius: int = 2) -> float:
        count = 0
        for other_id, (oy, ox) in self.agent_positions.items():
            if abs(oy - y) + abs(ox - x) <= radius and not (oy == y and ox == x):
                count += 1
        return float(count)

    def get_state(self) -> dict:
        return {
            "t": self.t,
            "agent_positions": {k: (int(v[0]), int(v[1])) for k, v in self.agent_positions.items()},
            "resources": self.resources.copy(),
            "obstacles": self.obstacles.copy(),
            "portals": self.portals.copy(),
            "cognitive_map": self.cognitive_map.copy(),
        }

    def set_state(self, state: dict):
        self.t = int(state["t"])
        self.agent_positions = {int(k): (int(v[0]), int(v[1])) for k, v in state["agent_positions"].items()}
        self.resources = state["resources"].copy()
        self.obstacles = state["obstacles"].copy()
        self.portals = state["portals"].copy()
        self.cognitive_map = state["cognitive_map"].copy()

    def _diffuse(self, arr: np.ndarray, strength: float) -> np.ndarray:
        kernel = np.array([[0.0, strength, 0.0], [strength, 1 - 4 * strength, strength], [0.0, strength, 0.0]], dtype=np.float32)
        out = np.copy(arr)
        padded = np.pad(arr, 1, mode="edge")
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                window = padded[i : i + 3, j : j + 3]
                out[i, j] = float(np.sum(window * kernel))
        return out
