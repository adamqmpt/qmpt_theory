from __future__ import annotations

import numpy as np


def cosine_continuity(vec1: np.ndarray, vec2: np.ndarray, eps: float = 1e-12) -> float:
    v1 = vec1.astype(np.float64).ravel()
    v2 = vec2.astype(np.float64).ravel()
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < eps or n2 < eps:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def behavior_divergence(actions_a, actions_b) -> float:
    if len(actions_a) != len(actions_b):
        raise ValueError("Action lists must have same length")
    if not actions_a:
        return 0.0
    diffs = sum(int(a != b) for a, b in zip(actions_a, actions_b))
    return diffs / len(actions_a)

