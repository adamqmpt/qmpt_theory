from __future__ import annotations

from typing import Sequence

import numpy as np
from numpy.typing import NDArray


def _flatten_pattern(pattern_state: dict) -> NDArray[np.float64]:
    internal = np.asarray(pattern_state["internal_state"], dtype=np.float64).ravel()
    W = np.asarray(pattern_state["W"], dtype=np.float64).ravel()
    return np.concatenate([internal, W]).astype(np.float64)


def continuity_cosine(
    pattern_state_1: dict, pattern_state_2: dict, eps: float = 1e-12
) -> float:
    """
    Cosine similarity between two pattern states.
    Values are in [-1, 1]; we focus on how close the score is to 1.0.
    """
    v1 = _flatten_pattern(pattern_state_1)
    v2 = _flatten_pattern(pattern_state_2)

    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < eps or n2 < eps:
        return 0.0

    return float(np.dot(v1, v2) / (n1 * n2))


def behavior_divergence(actions_1: Sequence[int], actions_2: Sequence[int]) -> float:
    """
    How differently two patterns behave on the same observation sequence.
    0.0 = identical behavior, 1.0 = actions differ at every step.
    """
    if len(actions_1) != len(actions_2):
        raise ValueError("Action sequences must have the same length.")
    if not actions_1:
        return 0.0
    diffs = sum(int(a1 != a2) for a1, a2 in zip(actions_1, actions_2))
    return diffs / len(actions_1)
