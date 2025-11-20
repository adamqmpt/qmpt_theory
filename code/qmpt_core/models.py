"""
Minimal QMPT data models for patterns and layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np


@dataclass
class Pattern:
    pattern_id: str
    layer_id: str
    features: Optional[np.ndarray] = None
    anomaly_score: Optional[float] = None
    reflexivity: Optional[float] = None
    self_operator: Optional[float] = None
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class LayerState:
    t: float
    stress: float
    protection: float
    novelty: float
    macro: Dict[str, object] = field(default_factory=dict)


@dataclass
class Layer:
    layer_id: str
    description: str = ""
    patterns: List[Pattern] = field(default_factory=list)
    trajectory: List[LayerState] = field(default_factory=list)
