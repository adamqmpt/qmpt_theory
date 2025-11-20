"""
Toy implementations of QMPT metrics.
Shape follows QMPT specs: A(Ψ), R_norm(Ψ), O_self(Ψ).
"""

from __future__ import annotations

from typing import List
import numpy as np

from .models import Pattern


def estimate_anomaly(patterns: List[Pattern]) -> None:
    """
    Compute a toy anomaly score:
    A = w1 * rarity + w2 * distance + w3 * impact

    rarity   ~ inverse feature norm
    distance ~ distance from mean feature vector
    impact   ~ free scalar from metadata ("impact" fallback to 0.1)
    """
    if not patterns:
        return
    feats = [p.features for p in patterns if p.features is not None]
    if not feats:
        for p in patterns:
            p.anomaly_score = 0.1
        return
    stacked = np.stack(feats)
    mean_vec = np.mean(stacked, axis=0)
    for p in patterns:
        if p.features is None:
            p.anomaly_score = 0.1
            continue
        rarity = 1.0 / (np.linalg.norm(p.features) + 1e-6)
        distance = float(np.linalg.norm(p.features - mean_vec))
        impact = float(p.metadata.get("impact", 0.1))
        p.anomaly_score = float(0.5 * rarity + 0.3 * distance + 0.2 * impact)


def estimate_reflexivity(patterns: List[Pattern]) -> None:
    """
    Toy reflexivity R_norm in [0,1]:
    R_norm = sigmoid(var(features)) where variance approximates self-model richness.
    """
    for p in patterns:
        if p.features is None:
            p.reflexivity = 0.2
            continue
        var = float(np.var(p.features))
        p.reflexivity = float(1.0 / (1.0 + np.exp(-var)))


def estimate_self_operator(patterns: List[Pattern]) -> None:
    """
    O_self = alpha_pop * Q_pop + alpha_self * Q_self + alpha_meta * Q_meta + alpha_R * R_norm.
    Here we synthesize Q_pop/Q_self/Q_meta from simple heuristics.
    """
    alpha_pop = 0.25
    alpha_self = 0.25
    alpha_meta = 0.25
    alpha_R = 0.25
    for p in patterns:
        rarity_proxy = 1.0 / (np.linalg.norm(p.features) + 1e-6) if p.features is not None else 0.1
        q_pop = min(1.0, rarity_proxy)
        q_self = min(1.0, abs(p.anomaly_score or 0.0) / 5.0)
        q_meta = min(1.0, (p.metadata.get("meta_consistency", 0.2)))
        r_norm = p.reflexivity or 0.0
        p.self_operator = float(alpha_pop * q_pop + alpha_self * q_self + alpha_meta * q_meta + alpha_R * r_norm)
