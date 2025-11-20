<!-- file: lab/qmpt_layer_anomaly_simulation_en.md -->

# QMPT Layer-Anomaly Simulation Framework (v0.2)

*A minimal but extensible mathematical and simulation framework for testing QMPT against historical data.*

---

## 1. Goal

The purpose of this document is to:

1. Formalize a **minimal core** of the QMPT model in a way that can be simulated.
2. Introduce additional variables beyond time and intensity:
   - layer complexity,
   - anomaly domains,
   - connectivity, sign, visibility,
   - recognition lag and feedback.
3. Describe how to compare:
   - a **QMPT-style model** (layer-driven anomalies),
   - against a **null model** (random “genius” arrivals).
4. Define **metrics and tests** that can be applied now (toy simulations) and later (real data).

This file is intentionally implementation-oriented: it should be possible to go from here to Python / R code without inventing missing structure.

---

## 2. Core hypotheses

We contrast two hypotheses:

- **H_QMPT (structured)**  
  Reality is organized as a **layer** with time-varying complexity \( C(t) \).  
  Rare **anomalous patterns** (people with layer-level impact) appear with an intensity that depends on the state of the layer and its infrastructure.  
  These anomalies:
  - cluster in time,
  - appear in different **domains** depending on epoch,
  - shorten their recognition lag as the layer becomes more complex.

- **H_0 (null / random geniuses)**  
  Influential figures appear as a **homogeneous or weakly inhomogeneous Poisson process** in time, with no strong coupling to layer complexity.  
  Clusters are explained by noise, survivorship bias and narrative selection.

The job of the simulation is not to “prove” H_QMPT, but to check:

> Does H_QMPT explain the **patterns we actually see** (clusters, domain shifts, lags) more naturally than H_0?

---

## 3. Variables and functions

Time is discrete in years: \( t \in [t_\min, t_\max] \), e.g. 1600–2100.

### 3.1. Layer complexity \( C(t) \)

A smooth function in \([0,1]\), approximating the **global complexity of the layer**:

- incorporates:
  - scientific/technical knowledge,
  - communication speed,
  - computational capacity,
  - institutional density.

Example (logistic core, to be calibrated later):

\[
C(t) = \frac{1}{1 + \exp(-(t - t_c)/\tau)}
\]

with parameters:

- \( t_c \) – inflection point (e.g. around 1850–1900),
- \( \tau \) – timescale of the transition.

### 3.2. Population and births \( B(t) \)

Approximate human births per year, scaled to a convenient unit:

- used to normalize **anomaly intensity per birth**, not only per year.
- at minimum: rough demographic curve (low and flat pre-1800, then rapid growth).

### 3.3. Infrastructure / connectivity level \( I(t) \)

A scalar in \([0,1]\) reflecting **how well ideas can propagate**:

- proxies: literacy, communication technology, urbanization.
- typically grows later than sheer population.

Often correlated with \( C(t) \) but not identical.

### 3.4. Domains \( D \)

Each anomaly belongs to exactly one domain \( d \in D \):

- `phys` – physical world (mechanics, fields, relativity, etc.),
- `life` – life/evolution/biological structure,
- `comp` – computation, formal systems, algorithms,
- `info` – information and communication theory,
- `sys` – systems/cybernetics/complexity,
- `ont` – ontology of reality, layers, simulation, consciousness.

For each time \( t \), we define **domain weights**:

\[
w_d(t) \ge 0,\quad \sum_{d \in D} w_d(t) = 1
\]

These encode which domain is “active” at which complexity range.  
For example, `phys` peaks at low \( C \), `comp` and `info` at mid \( C \), `ont` at high \( C \).

### 3.5. Anomaly intensity \( \lambda(t) \)

**Total intensity** of anomalies per unit time:

\[
\lambda_{\text{QMPT}}(t) = \lambda_0 \cdot f(C(t), I(t), B(t))
\]

Simplest first-order choice:

\[
\lambda_{\text{QMPT}}(t) = \lambda_0 \cdot (1 + \alpha_C C(t) + \alpha_I I(t))
\]

Null model:

\[
\lambda_0(t) = \text{const}
\]

or a weak trend not strongly coupled to \( C(t) \).

Per-domain intensity:

\[
\lambda_d(t) = \lambda_{\text{QMPT}}(t) \cdot w_d(t)
\]

### 3.6. Connectivity of an anomaly \( R \)

For each anomaly event \( i \) born at time \( t_i \), define:

- \( R_i \in [0,1] \): **connectivity** (how embedded the anomaly is in the infrastructure:
  - institutions,
  - access to tools and peers,
  - later: access to compute and AI.

We model:

\[
R_i \sim \text{Beta}(\alpha_R(C(t_i), I(t_i)), \beta_R(C(t_i), I(t_i)))
\]

High \( C \) and high \( I \) shift the distribution toward \( R \to 1 \).

### 3.7. Visibility / observability

Not every anomaly reaches the historical record. Define:

\[
\Pr(\text{observed } | R_i) = g(R_i)
\]

with a monotonically increasing function, e.g.:

\[
g(R) = R^\gamma,\quad \gamma \ge 1
\]

Events with low \( R \) become **latent anomalies**: they exist, but do not enter textbooks.

### 3.8. Sign of an anomaly

Each anomaly has a sign \( s_i \in \{-1, 0, +1\} \):

- \( +1 \): expands freedom/understanding/layer transparency,
- \( -1 \): expands control/oppression/optimized manipulation,
- \( 0 \): neutral or ambiguous.

We can define:

\[
\Pr(s_i = +1 \mid C(t_i)) = p_+(C(t_i)),\quad
\Pr(s_i = -1 \mid C(t_i)) = p_-(C(t_i)),
\]

with \( p_+ + p_- + p_0 = 1 \).

Basic hypothesis: \( p_+ \) increases with \( C \), as fully opaque control becomes harder in highly connected layers.

### 3.9. Recognition lag \( L \)

For each anomaly, define:

- birth time \( t_i \),
- recognition time \( t_i^{(rec)} = t_i + L_i \),

with \( L_i \ge 0 \) drawn from a distribution whose **mean decreases with complexity**:

\[
\mathbb{E}[L_i \mid C(t_i), I(t_i), R_i] = L_0 - \beta_C C(t_i) - \beta_I I(t_i) - \beta_R R_i,
\]

and actual lag:

\[
L_i \sim \text{Exponential}(\mu_i), \quad \mu_i = \mathbb{E}[L_i].
\]

### 3.10. Feedback on the layer

Optionally, anomalies can **feed back** into \( C(t) \):

\[
C(t + \Delta t) = C(t) + \sum_{i: t_i^{(rec)} \in [t, t+\Delta t)} \Delta C_i
\]

where \(\Delta C_i\) is a small increment depending on domain and sign:

- `phys`, `comp`, `info`, `sys`, `ont` may have different impact coefficients.

At early stages we can simulate without feedback (C fixed), then gradually add feedback.

---

## 4. Simulation pipeline (toy version)

### 4.1. Configuration

1. Choose time range \([t_\min, t_\max]\).
2. Specify functions:
   - \(C(t)\), \(I(t)\), \(B(t)\),
   - domain weights \( w_d(t) \),
   - intensity parameters \( \lambda_0, \alpha_C, \alpha_I \),
   - lag parameters \( L_0, \beta_C, \beta_I, \beta_R \),
   - sign probabilities \( p_+(C), p_-(C) \),
   - visibility function \( g(R) \).

3. Choose whether to:
   - include feedback of anomalies on \(C(t)\),
   - treat births explicitly or use per-year anomaly rates.

### 4.2. Generating anomalies

For each year \( t \):

1. Compute total intensity \( \lambda(t) \) (QMPT or null).
2. Sample number of anomalies:
   \[
   N_t \sim \text{Poisson}(\lambda(t))
   \]
3. For each of the \(N_t\) events:
   - sample precise birth time \( t_i = t + u \) with \( u \sim U(0,1) \),
   - compute \( C(t_i), I(t_i) \),
   - sample domain using \( w_d(t_i) \),
   - sample \( R_i \) from Beta,
   - sample sign \( s_i \) from \( p_+(C), p_-(C), p_0(C) \),
   - compute expected lag and sample \( L_i \),
   - compute recognition time \( t_i^{(rec)} \),
   - mark as observed with probability \( g(R_i) \).

### 4.3. Aggregation and metrics

From the synthetic dataset of events \( \{ t_i, d_i, s_i, R_i, L_i \} \) we compute:

- counts per 50-year bin for:
  - all anomalies,
  - by domain,
  - by sign,
  - observed vs latent.
- distribution of recognition lags \( L \) vs:
  - birth time,
  - \( C(t) \),
  - connectivity \( R \).
- “inequality” measures for temporal clustering:
  - Gini coefficient over time bins,
  - overdispersion relative to a homogeneous Poisson process.

---

## 5. Key patterns to check

### 5.1. Temporal clustering

We expect:

- Under **QMPT**, anomaly counts per time bin show:
  - clear increase with \( C(t) \),
  - visible clusters near phase transitions (e.g. 1850–1950).
- Under **H_0**, counts are roughly flat (up to mild trends).

**Tests:**

- Compare Gini coefficients over time between QMPT and null simulations.
- Use chi-squared or likelihood ratio tests to reject homogeneity.
- Apply change-point detection to see if rate shifts are significant.

### 5.2. Domain shifts

We expect domain dominance to **shift in stages**:

1. `phys` dominant at low complexity.
2. `comp` / `info` dominant at mid complexity.
3. `ont` dominant at high complexity.

**Tests:**

- For each domain, fit a peak in \( C \)-space and test whether peak positions follow the expected ordering.
- Check whether real historical data for “layer-shifters” show similar domain transition timing.

### 5.3. Recognition lag trends

We expect:

- mean recognition lag \( \mathbb{E}[L] \) to **decrease** with:
  - time,
  - layer complexity \( C(t) \),
  - connectivity \( R \).

**Tests:**

- Correlation and regression between \(L\) and \( C, I, R \).
- Compare lag distributions for early vs late epochs (e.g. 1700–1800 vs 1900–2000).

### 5.4. Positive vs negative anomalies

We expect:

- the fraction of “positive” anomalies to increase with \( C(t) \),
- but not necessarily monotonically in real data (war, crises, etc.).

**Tests:**

- If sign can be coded for historical figures, estimate \( p_+(t) \) empirically and test correlation with proxies of complexity.

---

## 6. From toy simulations to real data

### 6.1. Data to collect

To move beyond synthetic tests, QMPT should be confronted with a real dataset, including:

- A curated list (100–500 cases) of **layer-impacting individuals** across:
  - physics, math, biology, computation, information, systems, ontology/philosophy of reality.
- For each:
  - year of birth,
  - approximate “breakthrough” year,
  - domain(s),
  - region/infrastructure level (rough rating),
  - approximate recognition lag (time to adoption or impact),
  - optional sign label (+ / – / neutral).

Control group:

- comparable list of “major scientists” whose work **did not** deeply shift the layer model.

### 6.2. Calibration and validation

1. Use data from 1600–1950 to **calibrate**:
   - plausible shapes for \( C(t), I(t) \),
   - coefficients \( \alpha_C, \alpha_I, L_0, \beta_C, \beta_I \),
   - approximate domain weights.
2. Simulate 1950–2025 and compare distributions of:
   - anomaly counts,
   - domain composition,
   - recognition lags,
   - clustering metrics.
3. Use 2025+ as a **prediction window**:
   - e.g. forecast the expected number and type of ontology-level anomalies up to 2050.

---

## 7. What is critical for further work

To make the simulation scientifically meaningful, the following elements are key:

1. **Explicit definitions** of “layer-shifter” vs “ordinary major scientist”.
2. **Transparent parametrization** of \( C(t), I(t) \) using real indicators:
   - publication volume, patents, compute, communication speed, etc.
3. **Robustness checks**:
   - do results hold under variations of model structure?
   - can simpler H_0 variants match the same patterns without fine tuning?
4. **Falsifiable predictions**:
   - about clustering, domain transition timing, recognition lag trends.

If QMPT-style models continue to match historical patterns **better** than null models across multiple metrics, they become not just a philosophical story but a **testable meta-model of the evolution of anomalous minds and layers.**

---

## 8. Next steps

1. Implement this framework in code (Python, R, or Julia).
2. Run **systematic simulations** under:
   - H_QMPT with different parameter sets,
   - H_0 (and a couple of intermediate baselines).
3. Publish:
   - code,
   - simulation notebooks,
   - and eventually a dataset with layer-impacting figures and metrics.
4. Iterate QMPT’s formal core based on mismatches between model and history.

This document is the **specification layer**: the simulations and empirical evaluation are the next layers on top of it.
