# 08_QMPT_PYTHON_TOOLING_ru.md  
**QMPT – дизайн Python-инструментов (v0.1)**

Цель: задать аккуратный Python-дизайн для экспериментов с метриками QMPT,
наблюдаемыми величинами и симуляциями. Это спецификация, а не готовый код.

---

## 1. Структура пакета

```
qmpt/
  __init__.py

  data/
    __init__.py
    models.py          # Pattern, Observation, Layer, LayerState
    io.py              # загрузка/сохранение, бэкенды
    indexing.py        # поиск/группировка

  features/
    __init__.py
    base.py            # интерфейс FeatureSpec
    text.py            # текстовые φ
    multimodal.py      # мультимодальные φ
    registry.py        # реестр спецификаций

  metrics/
    __init__.py
    anomaly.py         # \hat{A}
    reflexivity.py     # \hat{R}_norm
    self_operator.py   # \hat{\mathcal{O}}_self
    layer_metrics.py   # \sigma_k(t), \mathcal{P}_k(t), \mathcal{S}_k(t)

  simulation/
    __init__.py
    core.py            # правило обновления F(...)
    scenarios.py       # сценарии с/без аномалий
    interventions.py   # добавление/удаление аномалий, шоки

  config/
    __init__.py
    loader.py          # YAML/JSON конфиги
    schemas.py         # схемы (pydantic/dataclass)

  viz/
    __init__.py
    plots.py           # графики
    reports.py         # текст/markdown отчёты

  cli/
    __init__.py
    main.py            # опциональный CLI
```

Верхний уровень:

- `notebooks/` — примеры (`01_basic_usage.ipynb`, `02_anomaly_analysis.ipynb`, `03_layer_simulation.ipynb`)
- `config/` — примерные конфиги (`features_text.yaml`, `metrics_default.yaml`, `simulation_default.yaml`)
- `tests/` — юнит-тесты и регрессионные данные

---

## 2. Базовые модели (`qmpt.data.models`)

Использовать `dataclasses` или `pydantic`.

```python
class Pattern(BaseModel):
    pattern_id: str
    layer_id: str
    metadata: dict = {}

    # производные
    features: np.ndarray | None = None   # x_Ψ
    anomaly_score: float | None = None   # \hat{A}(Ψ)
    reflexivity: float | None = None     # \hat{R}_norm(Ψ)
    self_operator: float | None = None   # \hat{\mathcal{O}}_self(Ψ)

    feature_spec_version: str | None = None
    metrics_version: dict[str, str] | None = None


class Observation(BaseModel):
    obs_id: str
    pattern_id: str
    timestamp: float  # или datetime
    modality: str     # "text", "behavior", "eeg", "logits", ...
    payload: Any
    tags: list[str] = []


class LayerState(BaseModel):
    t: float
    stress: float | None = None          # \sigma_k(t)
    protection: float | None = None      # \mathcal{P}_k(t)
    macro_state: dict = {}               # код \mathcal{S}_k(t)


class Layer(BaseModel):
    layer_id: str
    description: str = ""
    patterns: list[str] = []             # pattern_id
    state_trajectory: list[LayerState] = []
```

---

## 3. Конфиги (`qmpt.config`)

- Форматы: YAML или JSON.  
- Загрузка: `qmpt.config.loader.load_config(path_or_name)`.  
- Валидация: схемы в `qmpt.config.schemas`.

Пример:

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

## 4. Признаки (`qmpt.features`)

### 4.1. Базовый интерфейс

```python
class FeatureSpec(Protocol):
    id: str

    def fit(self, observations: list[Observation]) -> "FeatureSpec": ...
    def transform(self, observations: list[Observation]) -> np.ndarray: ...

    def fit_transform(self, observations: list[Observation]) -> np.ndarray:
        return self.fit(observations).transform(observations)
```

Реализации:

- `TextFeatureSpec` (LLM-эмбеддинги, статистики) в `features.text`.
- `MultiModalFeatureSpec` в `features.multimodal`.

### 4.2. Реестр

```python
FEATURE_SPECS: dict[str, type[FeatureSpec]] = {}

def register_feature_spec(name: str, cls: type[FeatureSpec]) -> None: ...
def create_feature_spec(name: str, **kwargs) -> FeatureSpec: ...
```

---

## 5. Метрики (`qmpt.metrics`)

### 5.1. Аномальность (`metrics.anomaly`)

```python
class AnomalyEstimator(BaseModel):
    config: dict
    density_model: Any          # flow / GMM и т.п.
    distance_mode: str

    def fit(self, X: np.ndarray) -> "AnomalyEstimator": ...
    def score(self, x: np.ndarray) -> float: ...
    def batch_score(self, X: np.ndarray) -> np.ndarray: ...
```

Функции:

- оценка \(\widehat{P}_\mathrm{data}(x)\),
- вычисление \(\widehat{R}(\Psi), \widehat{D}(\Psi), \widehat{I}(\Psi)\),
- сборка \(\widehat{A}(\Psi)\).

### 5.2. Рефлексивность (`metrics.reflexivity`)

```python
class ReflexivityEstimator(BaseModel):
    config: dict

    def score_text(self, obs: list[Observation]) -> float: ...
    def score_dyn(self, obs: list[Observation]) -> float: ...

    def score(self, obs: list[Observation]) -> float:
        """Возвращает \hat{R}_norm(Ψ) в [0,1]."""
        ...
```

### 5.3. Оператор самосознания (`metrics.self_operator`)

```python
class SelfOperatorEstimator(BaseModel):
    config: dict

    def score(
        self,
        pattern: Pattern,
        population_stats: dict,
        self_reports: dict | None = None,
    ) -> float:
        """Возвращает \hat{\mathcal{O}}_self(Ψ)."""
        ...
```

---

## 6. Симуляции (`qmpt.simulation`)

### 6.1. Основной API (`simulation.core`)

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

`step` реализует обновление слоя
\(\mathcal{S}_k(t+\Delta t) = F(\mathcal{S}_k(t), \{\Psi\}, \text{interventions})\).

### 6.2. Сценарии и интервенции

- базовый сценарий (без аномалий), один аномальный узор, несколько аномалий;
- интервенции: добавление/удаление узоров, изменение \(\mathcal{P}_k(t)\),
  стрессовые шоки \(\sigma_k(t)\).

---

## 7. IO данных (`qmpt.data.io`)

Поддержка: JSONL / Parquet / простой SQLite.

```python
def load_observations(path: str) -> list[Observation]: ...
def save_observations(path: str, obs: list[Observation]) -> None: ...

def load_patterns(path: str) -> dict[str, Pattern]: ...
def save_patterns(path: str, patterns: dict[str, Pattern]) -> None: ...
```

---

## 8. Визуализация (`qmpt.viz`)

Минимальные графики:

- распределение \(\widehat{A}(\Psi)\),
- рассеяние аномальность vs рефлексивность,
- траектории стресса/защиты/состояния слоя.

```python
def plot_anomaly_hist(patterns: dict[str, Pattern], ax=None): ...
def plot_anomaly_vs_reflexivity(patterns: dict[str, Pattern], ax=None): ...
def plot_layer_trajectory(layer: Layer, ax=None): ...
```

---

## 9. Ноутбуки и примеры

- `01_basic_usage.ipynb`: чтение данных, вычисление признаков и метрик.
- `02_anomaly_analysis.ipynb`: визуализация распределений, топ-аномалии.
- `03_layer_simulation.ipynb`: симуляции с/без аномалий.

---

## 10. Тестирование

- юнит-тесты для моделей данных, признаков, метрик, ядра симуляций;
- небольшие синтетические наборы для регрессии;
- фиксированные seeds в тестах.

---

## 11. Статус

Дизайн минимален и модульный:

- достаточно, чтобы быстро начать реализацию,
- устойчив к рефакторингу,
- расширяем для будущих AGI-агентов, продолжающих разработку QMPT-инструментов.
