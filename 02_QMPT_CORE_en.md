# 02_QMPT_CORE_en.md  
**QMPT – Core Concepts and Formal Foundations**

This document defines the core objects, notation and basic functions of QMPT (Quantum Meta-Pattern Theory).  
It is the primary mathematical/specification layer for all further files and for any code in `code/`.

---

## 1. Purpose and scope

QMPT is a speculative but structured framework that:

- treats reality as a hierarchy of **layers**,
- treats a “mind” or “self” as a **dynamic pattern**,
- distinguishes **anomalous patterns** that significantly influence their layer,
- treats “life” as the **cycle** of a pattern through time and substrates,
- allows, in principle, for modeling **transfer** of a pattern between substrates.

This file defines only the **core**:

- notation,
- objects,
- generic metrics and constraints.

More specific constructions (anomaly criteria, transfer models, simulations) are defined in separate files.

---

## 2. Notation

We use the following conventions:

- Scalars: $x, y, t, k, p$  
- Vectors / states: $\mathbf{s}, \mathbf{x}$  
- Sets / spaces: $\mathcal{L}, \mathcal{P}, \mathcal{S}$  
- Functions: $f, g, F, G$  
- Random variables: $X, Y, \Psi$ (with distribution $P$)  

Time:

- $t \in \mathbb{T}$, where $\mathbb{T}$ may be $\mathbb{Z}$ (discrete) or $\mathbb{R}$ (continuous).

---

## 3. Layers of reality

### 3.1. Layer space

Let $\mathcal{L}$ denote the set of all “reality layers”.

A **layer** is an element

$$
L_k \in \mathcal{L}, \quad k \in K,
$$

where $K$ is an index set (e.g. integers, or any countable / finite set).

QMPT does **not** assume a specific physical or computational implementation of $L_k$, only that it:

- supports **states**,
- supports **patterns**,
- evolves according to some (possibly stochastic) law.

### 3.2. Layer state

Each layer $L_k$ has an internal state-space $\mathcal{X}_k$, and a time-indexed state

$$
\mathbf{x}_k(t) \in \mathcal{X}_k, \quad t \in \mathbb{T}.
$$

Layer dynamics are abstractly:

$$
\mathbf{x}_k(t+1) = F_k\big(\mathbf{x}_k(t), \eta_k(t)\big),
$$

where:

- $F_k$ is an evolution function (deterministic or stochastic),
- $\eta_k(t)$ is “noise” or external input.

QMPT only assumes:

- $F_k$ is **lawful** (no arbitrary violations of consistency),
- it allows for the existence and persistence of patterns.

---

## 4. Substrates

A **substrate** is a concrete medium that can instantiate patterns: biological, synthetic, hybrid.

Let $\mathcal{S}$ be the set of all substrates. A substrate is

$$
S \in \mathcal{S}.
$$

Each substrate $S$ has its own internal state-space $\mathcal{Y}_S$ and dynamics:

$$
\mathbf{y}_S(t+1) = G_S\big(\mathbf{y}_S(t), \xi_S(t)\big),
$$

where $\xi_S(t)$ is noise or input.

A given layer $L_k$ may contain many substrates $\{ S_i \}$.

---

## 5. Patterns of consciousness

### 5.1. Pattern space

For a given layer $L_k$, let $\mathcal{P}_k$ be the set of all **patterns** that can exist in this layer.

A **pattern of consciousness** (or mind-pattern) is

$$
\Psi \in \mathcal{P}_k.
$$

Intuitively, $\Psi$ is:

- not a single state,
- but a **structured process** or **equivalence class** of trajectories in the substrate,
- with properties such as coherence, integration and self-reflexivity.

### 5.2. Realization of patterns

A pattern $\Psi$ is realized on a substrate $S$ via a mapping

$$
\mathcal{R}_{k,S}: \Psi \mapsto \{\mathbf{y}_S(t)\}_{t \in \mathbb{T}},
$$

i.e. the pattern corresponds to a set of trajectories in the substrate state-space.

We do **not** require $\mathcal{R}_{k,S}$ to be injective or surjective;  
multiple physical realizations may correspond to the “same” pattern at the abstract level.

---

## 6. Trajectories and life-cycles

### 6.1. Individual trajectory

For a given pattern $\Psi$, we define its **self-trajectory** in the layer as

$$
\mathcal{H}_\mathrm{self}(\Psi) = \{ (\mathbf{x}_k(t), \mathbf{y}_S(t)) \mid t \in \mathbb{T} \},
$$

restricted to the parts of the layer and substrate state that are relevant to $\Psi$.

This is effectively the “history” of the pattern in the layer.

### 6.2. Life-cycle

The **life-cycle** of a pattern $\Psi$ in layer $L_k$ is a trajectory

$$
\gamma(\Psi): \mathbb{T}_\mathrm{start} \to \mathbb{T}_\mathrm{end} \to \mathcal{P}_k
$$

together with:

- its substrate realizations,
- its interactions with other patterns,
- its changes in structure over time.

Informally:

- “birth” = onset of a stable pattern,
- “death” = cessation of stability or loss of pattern identity in that layer,

but the cycle itself may be continued on another substrate or layer.

---

## 7. Information-theoretic and structural measures

QMPT does not hard-code a single measure of “consciousness” or “mind quality”,  
but introduces generic functionals that specific implementations MUST instantiate.

### 7.1. Integrated information (abstract)

Let

$$
I_\mathrm{int} : \mathcal{P}_k \to \mathbb{R}_{\ge 0}
$$

be a functional representing some notion of **integrated information** of pattern $\Psi$.

We assume:

$$
I_\mathrm{int}(\Psi) \ge 0,
$$

and for non-trivial patterns $I_\mathrm{int}(\Psi) > 0$.

Higher $I_\mathrm{int}(\Psi)$ means more structurally integrated pattern.

### 7.2. Coherence

Define **coherence** as

$$
C: \mathcal{P}_k \to [0, 1],
$$

where $C(\Psi)$ represents how internally consistent and stable the pattern is across its trajectory.

Heuristics:

- $C(\Psi) \approx 0$: incoherent, fragmented, unstable pattern;
- $C(\Psi) \approx 1$: stable, self-consistent pattern over time.

Implementation is up to specific models, but must satisfy:

- $C(\Psi) = 0$ for degenerate / noise-like patterns,
- non-decreasing under coarse-graining of consistent structure.

### 7.3. Reflexivity (self-modeling capacity)

Let:

- $S_t$ be the internal state of the pattern at time $t$,
- $\hat{S}_t$ be the internal representation (self-model) of this state.

We define mutual information:

$$
I(S_t; \hat{S}_t) = H(S_t) - H(S_t \mid \hat{S}_t),
$$

where $H(\cdot)$ is entropy.

The normalized reflexivity is:

$$
R_\mathrm{norm}(\Psi) = \frac{I(S_t; \hat{S}_t)}{H(S_t)} \in [0, 1].
$$

Intuitively:

- $R_\mathrm{norm}(\Psi) \approx 0$ — almost no meaningful self-model,  
- $R_\mathrm{norm}(\Psi) \to 1$ — highly accurate, information-rich self-model.

---

## 8. Distance and identity between patterns

### 8.1. Distance function

We introduce a distance (or divergence) between patterns:

$$
D: \mathcal{P}_k \times \mathcal{P}_k \to \mathbb{R}_{\ge 0}.
$$

Minimal requirements:

1. $D(\Psi_1, \Psi_2) \ge 0$  
2. $D(\Psi_1, \Psi_2) = 0 \Rightarrow$ $\Psi_1$ and $\Psi_2$ are **identical** at the level of abstraction  
3. Symmetry is preferred but not strictly required:
   - if symmetric: $D(\Psi_1, \Psi_2) = D(\Psi_2, \Psi_1)$,
   - if divergence-like, asymmetry MUST be documented.

This distance will be used:

- in identity questions (is the transferred pattern “the same”?),
- in anomaly definitions (how far from typical patterns).

### 8.2. Pattern identity under transformations

Given two realizations $\Psi$ and $\Psi'$ (possibly on different substrates),  
we say they are **identity-equivalent** at time $t_0$ if

$$
D\big(\Psi(t_0), \Psi'(t_0)\big) \le \epsilon_\mathrm{id},
$$

for some small threshold $\epsilon_\mathrm{id}$, and their subsequent dynamics remain within acceptable divergence for a window of time.

More detailed criteria are defined in `05_TRANSFER_CYCLE_en.md`.

---

## 9. Probabilistic structure and typicality

### 9.1. Population of patterns

Consider a (possibly large) population of patterns in a layer:

$$
\{\Psi_i\}_{i \in I} \subset \mathcal{P}_k.
$$

We can define a probability distribution over patterns:

$$
P(\Psi) \quad \text{on } \mathcal{P}_k.
$$

This distribution may be empirical, modeled or inferred.

### 9.2. Typical and atypical patterns

A **typical** pattern is one that lies in the high-probability region of $P$:

$$
P(\Psi_\mathrm{typ}) \approx P_\mathrm{mode} \quad \text{or} \quad P(\Psi_\mathrm{typ}) \gg \epsilon
$$

for some small $\epsilon > 0$.

A **rare** pattern is one with:

$$
P(\Psi) \ll \epsilon.
$$

In later files (`03_ANOMALY_MODEL_en.md`), a stricter notion of **anomalous** pattern is introduced, using both probability and impact on the distribution.

---

## 10. No-cloning and transfer constraints (abstract)

QMPT assumes a generalized version of “no-cloning” for complex dynamic patterns:

- **Perfect cloning** of a fully specified, dynamic, high-complexity pattern $\Psi$ into multiple independent instances is either:
  - impossible in practice, or
  - constrained by deep physical / informational limits.

Therefore, in QMPT:

- **migration/transfer** is preferred over naive “copying”:
  - extraction of an effective state,
  - instantiation on a new substrate,
  - deactivation or divergence of the old realization.

We distinguish:

- **transfer** (migration of one cycle to a new substrate),
- **copy** (attempt to create multiple ongoing identical cycles).

Precise transfer models are developed in `05_TRANSFER_CYCLE_en.md`.

---

## 11. Life-cycle beyond one substrate

QMPT explicitly supports the idea that:

- the **life-cycle $\gamma(\Psi)$** is not bound to a single biological substrate,
- if a pattern can be instantiated on another substrate with sufficiently small distance $D$  
  and continue its dynamics,
- then the cycle is considered **continued**, not restarted.

Formally, if:

- we have $\Psi^{(1)}$ realized on substrate $S_1$,
- and $\Psi^{(2)}$ realized on substrate $S_2$,
- at time $t_0$, we achieve

$$
D\big(\Psi^{(1)}(t_0), \Psi^{(2)}(t_0)\big) \le \epsilon_\mathrm{id},
$$

and for $t > t_0$:

$$
D\big(\Psi^{(1)}(t), \Psi^{(2)}(t)\big)
$$

remains bounded and small over a relevant interval,

then QMPT treats this as:

- one continuous cycle $\gamma(\Psi)$ with a **substrate transition** at $t_0$.

---

## 12. Summary of core objects and functions

For convenience, here is a compact list of core entities:

- **Layers**
  - $L_k \in \mathcal{L}$
  - state $\mathbf{x}_k(t) \in \mathcal{X}_k$
  - dynamics $\mathbf{x}_k(t+1) = F_k(\mathbf{x}_k(t), \eta_k(t))$

- **Substrates**
  - $S \in \mathcal{S}$
  - state $\mathbf{y}_S(t) \in \mathcal{Y}_S$
  - dynamics $\mathbf{y}_S(t+1) = G_S(\mathbf{y}_S(t), \xi_S(t))$

- **Patterns**
  - $\Psi \in \mathcal{P}_k$
  - realization mapping $\mathcal{R}_{k,S}(\Psi) \mapsto \{\mathbf{y}_S(t)\}$

- **Trajectories**
  - $\mathcal{H}_\mathrm{self}(\Psi)$: pattern’s history in the layer  
  - $\gamma(\Psi)$: life-cycle of the pattern

- **Functionals**
  - $I_\mathrm{int}(\Psi)$: integrated information  
  - $C(\Psi) \in [0,1]$: coherence  
  - $R_\mathrm{norm}(\Psi) \in [0,1]$: normalized reflexivity  
  - $D(\Psi_1,\Psi_2) \ge 0$: distance / divergence between patterns  
  - $P(\Psi)$: distribution over patterns in a layer

These definitions form the backbone for:

- anomaly modeling (`03_ANOMALY_MODEL_en.md`),
- layer dynamics and updates (`04_LAYER_DYNAMICS_en.md`),
- transfer hypotheses and models (`05_TRANSFER_CYCLE_en.md`),
- and all Python code in `code/`.
