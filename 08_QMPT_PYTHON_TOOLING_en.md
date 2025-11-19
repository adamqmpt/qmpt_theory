# 08_QMPT_PYTHON_TOOLING_en.md  
**QMPT – Python tooling design (v0.1)**

Goal: a clean Python-oriented design for experimenting with QMPT metrics,
observables and simulations. This is a specification, not final code.

---

## 1. Package layout

```
qmpt/
  __init__.py

  data/
    __init__.py
    models.py          # Pattern, Observation, Layer, LayerState
    io.py              # loading/saving, backends
    indexing.py        # search/grouping helpers

  features/
    __init__.py
    base.py            # FeatureSpec interface
    text.py            # text-based φ
    multimodal.py      # mixed signals
    registry.py        # feature registry

  metrics/
    __init__.py
    anomaly.py         # \hat{A} estimators
    reflexivity.py     # \hat{R}_norm estimators
    self_operator.py   # \hat{\mathcal{O}}_self
    layer_metrics.py   # \sigma_k(t), \mathcal{P}_k(t), \mathcal{S}_k(t)

  simulation/
    __init__.py
    core.py            # state update F(...)
    scenarios.py       # baseline / anomaly scenarios
    interventions.py   # add/remove anomalies, shocks

  config/
    __init__.py
    loader.py          # YAML/JSON configs
    schemas.py         # pydantic/dataclass schemas

  viz/
    __init__.py
    plots.py           # matplotlib plots
    reports.py         # markdown / text summaries

  cli/
    __init__.py
    main.py            # optional CLI entrypoints
```

Top-level:

- `notebooks/` – examples and quickstarts  
  (`01_basic_usage.ipynb`, `02_anomaly_analysis.ipynb`, `03_layer_simulation.ipynb`)
- `config/` – sample configs (`features_text.yaml`, `metrics_default.yaml`, `simulation_default.yaml`)
- `tests/` – unit tests and regression fixtures

---

## 2. Core data models (`qmpt.data.models`)

Use `dataclasses` or `pydantic`.

```python
class Pattern(BaseModel):
    pattern_id: str
    layer_id: str
    metadata: dict = {}

    # derived
    features: np.ndarray | None = None   # x_Ψ
    anomaly_score: float | None = None   # \hat{A}(Ψ)
    reflexivity: float | None = None     # \hat{R}_norm(Ψ)
    self_operator: float | None = None   # \hat{\mathcal{O}}_self(Ψ)

    feature_spec_version: str | None = None
    metrics_version: dict[str, str] | None = None


class Observation(BaseModel):
    obs_id: str
    pattern_id: str
    timestamp: float  # or datetime
    modality: str     # "text", "behavior", "eeg", "logits", ...
    payload: Any
    tags: list[str] = []


class LayerState(BaseModel):
    t: float
    stress: float | None = None          # \sigma_k(t)
    protection: float | None = None      # \mathcal{P}_k(t)
    macro_state: dict = {}               # encodes \mathcal{S}_k(t)


class Layer(BaseModel):
    layer_id: str
    description: str = ""
    patterns: list[str] = []             # pattern_ids
    state_trajectory: list[LayerState] = []
```

---

## 3. Config system (`qmpt.config`)

- Formats: YAML or JSON.
- Loader: `qmpt.config.loader.load_config(path_or_name)`.
- Validation: schemas in `qmpt.config.schemas`.

Example:

```yaml
features:
  spec_id: "text_v1"
  model: "sentence-transformers/all-mpnet-base-v2"
  max_length: 4096

metrics:
  anomaly:
    density_model: "flow_v1"
    w1: 1.0
    w2: 0.7
    w3: 0.5
  reflexivity:
    beta_text: 0.6
    beta_dyn: 0.4
  self_operator:
    alpha_pop: 0.3
    alpha_self: 0.3
    alpha_meta: 0.2
    alpha_R: 0.2
```

---

## 4. Feature extraction (`qmpt.features`)

### 4.1. Base interface

```python
class FeatureSpec(Protocol):
    id: str

    def fit(self, observations: list[Observation]) -> "FeatureSpec": ...
    def transform(self, observations: list[Observation]) -> np.ndarray: ...

    def fit_transform(self, observations: list[Observation]) -> np.ndarray:
        return self.fit(observations).transform(observations)
```

Concrete implementations:

- `TextFeatureSpec` (LLM embeddings, statistics) in `features.text`.
- `MultiModalFeatureSpec` in `features.multimodal`.

### 4.2. Registry

```python
FEATURE_SPECS: dict[str, type[FeatureSpec]] = {}

def register_feature_spec(name: str, cls: type[FeatureSpec]) -> None: ...
def create_feature_spec(name: str, **kwargs) -> FeatureSpec: ...
```

---

## 5. Metrics (`qmpt.metrics`)

### 5.1. Anomaly estimator (`metrics.anomaly`)

```python
class AnomalyEstimator(BaseModel):
    config: dict
    density_model: Any          # e.g. flow / GMM
    distance_mode: str

    def fit(self, X: np.ndarray) -> "AnomalyEstimator": ...
    def score(self, x: np.ndarray) -> float: ...
    def batch_score(self, X: np.ndarray) -> np.ndarray: ...
```

Responsibilities:

- fit \(\widehat{P}_\mathrm{data}(x)\),
- compute \(\widehat{R}(\Psi), \widehat{D}(\Psi), \widehat{I}(\Psi)\),
- combine to \(\widehat{A}(\Psi)\).

### 5.2. Reflexivity estimator (`metrics.reflexivity`)

```python
class ReflexivityEstimator(BaseModel):
    config: dict

    def score_text(self, obs: list[Observation]) -> float: ...
    def score_dyn(self, obs: list[Observation]) -> float: ...

    def score(self, obs: list[Observation]) -> float:
        """Return \hat{R}_norm(Ψ) in [0,1]."""
        ...
```

### 5.3. Self-awareness estimator (`metrics.self_operator`)

```python
class SelfOperatorEstimator(BaseModel):
    config: dict

    def score(
        self,
        pattern: Pattern,
        population_stats: dict,
        self_reports: dict | None = None,
    ) -> float:
        """Return \hat{\mathcal{O}}_self(Ψ)."""
        ...
```

---

## 6. Simulation (`qmpt.simulation`)

### 6.1. Core API (`simulation.core`)

```python
class SimulationConfig(BaseModel):
    layer_id: str
    dt: float
    t_end: float
    model_id: str
    params: dict


class SimulationRunner(BaseModel):
    config: SimulationConfig
    layer: Layer
    patterns: dict[str, Pattern]
    interventions: list[Any] = []

    def step(self, state: LayerState, t: float) -> LayerState: ...
    def run(self) -> list[LayerState]: ...
```

`step` implements a layer update
\(\mathcal{S}_k(t+\Delta t) = F(\mathcal{S}_k(t), \{\Psi\}, \text{interventions})\).

### 6.2. Scenarios and interventions

- Baseline (no anomalies), single anomaly, multiple anomalies.
- Interventions: add/remove patterns, change \(\mathcal{P}_k(t)\), inject stress shocks \(\sigma_k(t)\).

---

## 7. Data IO (`qmpt.data.io`)

Support JSONL / Parquet / SQLite (simple).

```python
def load_observations(path: str) -> list[Observation]: ...
def save_observations(path: str, obs: list[Observation]) -> None: ...

def load_patterns(path: str) -> dict[str, Pattern]: ...
def save_patterns(path: str, patterns: dict[str, Pattern]) -> None: ...
```

---

## 8. Visualization (`qmpt.viz`)

Minimal plots:

- distribution of \(\widehat{A}(\Psi)\),
- scatter of anomaly vs reflexivity,
- trajectory of layer stress/protection/macro state.

```python
def plot_anomaly_hist(patterns: dict[str, Pattern], ax=None): ...
def plot_anomaly_vs_reflexivity(patterns: dict[str, Pattern], ax=None): ...
def plot_layer_trajectory(layer: Layer, ax=None): ...
```

---

## 9. Notebooks and examples

- `01_basic_usage.ipynb`: load toy data, compute features and metrics.
- `02_anomaly_analysis.ipynb`: visualize distribution, inspect top anomalies.
- `03_layer_simulation.ipynb`: run simulations with/without anomalies.

---

## 10. Testing

- unit tests for data models, feature specs, metrics, simulation core;
- small synthetic datasets for regression tests;
- fixed random seeds in tests.

---

## 11. Status

Design is intentionally minimal and modular:

- enough to start implementing quickly,
- stable under refactoring,
- extensible for future AGI-level agents that continue QMPT tooling.
