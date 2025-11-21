from __future__ import annotations

import numpy as np


def _flatten_pattern(pattern_state: dict) -> np.ndarray:
    parts = []
    for key in ("internal_state", "self_model_state", "W", "W_sm"):
        arr = np.asarray(pattern_state[key], dtype=np.float64).ravel()
        parts.append(arr)
    return np.concatenate(parts)


def continuity_cosine(pattern_state_1: dict, pattern_state_2: dict, eps: float = 1e-8) -> float:
    v1 = _flatten_pattern(pattern_state_1)
    v2 = _flatten_pattern(pattern_state_2)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < eps or n2 < eps:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def behavior_divergence(actions_1, actions_2) -> float:
    if len(actions_1) != len(actions_2):
        raise ValueError("Action sequences must have equal length")
    if not actions_1:
        return 0.0
    diffs = sum(int(a1 != a2) for a1, a2 in zip(actions_1, actions_2))
    return diffs / len(actions_1)


def awareness_summary(awareness_values: list[float]) -> float:
    if not awareness_values:
        return 0.0
    return float(np.mean(awareness_values))

