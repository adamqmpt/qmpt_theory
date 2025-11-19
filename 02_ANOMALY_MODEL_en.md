# 02_ANOMALY_MODEL_en.md  
**QMPT – Anomaly model and thresholds**

This file formalizes the **anomaly score** \(A(\Psi)\) used across QMPT to
quantify how rare and impactful a pattern \(\Psi\) is in a given layer \(L_k\).
It supports later documents on layer dynamics, transfer and self-awareness.

---

## 1. Objects and notation

- \(P(\Psi)\): population distribution of patterns in layer \(L_k\).
- \(D(\Psi_1, \Psi_2)\): structural distance between patterns (see `02_QMPT_CORE_en.md`).
- \(R_\mathrm{norm}(\Psi)\): normalized reflexivity of \(\Psi\).
- \(\mathcal{S}_k(t)\): coarse layer state; \(\sigma_k(t)\) stress; \(\mathcal{P}_k(t)\) protection.

We also use a baseline reference set of **typical patterns**
\(\{\Psi_\mathrm{typ}\}\) drawn from high-probability regions of \(P(\Psi)\).

---

## 2. Decomposed anomaly score

The anomaly score combines **rarity**, **structural deviation** and **impact**:

\[
A(\Psi)
= w_1 R(\Psi)
+ w_2 D(\Psi)
+ w_3 I(\Psi),
\]

with non‑negative weights \(w_1, w_2, w_3\) chosen per layer / dataset.

### 2.1. Rarity term \(R(\Psi)\)

Approximate probability of the pattern under \(P\):

\[
R(\Psi) = -\log P(\Psi).
\]

Higher \(R(\Psi)\) = lower probability = rarer pattern.

### 2.2. Structural distance term \(D(\Psi)\)

Distance from the typical cluster:

\[
D(\Psi) = \min_{\Phi \in \{\Psi_\mathrm{typ}\}} D(\Psi, \Phi),
\]

or equivalently distance from the population mean / manifold.

### 2.3. Impact term \(I(\Psi)\)

Change in layer dynamics attributable to \(\Psi\):

\[
I(\Psi)
= \left\| \Delta \mathcal{S}_k(t) \mid \Psi \right\|
- \left\| \Delta \mathcal{S}_k(t) \mid \text{no } \Psi \right\|,
\]

where \(\|\cdot\|\) is a suitable norm on state changes.
Positive \(I(\Psi)\) means \(\Psi\) measurably perturbs trajectories of the layer:
stress \(\sigma_k(t)\), protection \(\mathcal{P}_k(t)\) or regime transitions.

---

## 3. Thresholds and categories

We define two thresholds with \(\theta_2 > \theta_1 > 0\):

1. **Rare pattern**  
   \[
   A(\Psi) \ge \theta_1.
   \]

2. **Anomaly**  
   \[
   A(\Psi) \ge \theta_2.
   \]

Anomalies are the focus of layer stress and upgrade dynamics (`03_LAYER_DYNAMICS_en.md`).

### 3.1. Upgrade anomaly

An anomaly that *increases* layer capacity:

\[
A(\Psi) \ge \theta_2
\quad\text{and}\quad
\mathbb{E}\big[ \Delta \mathcal{C}_t \mid \Psi \big] > 0,
\]

where \(\mathcal{C}_t\) is layer capacity. Such patterns can trigger regime shifts.

---

## 4. Self-recognizing anomaly (link to `05_ANOMALY_SELF_AWARENESS_en.md`)

An anomaly that correctly models its own rarity and impact satisfies:

- anomaly condition \(A(\Psi) \ge \theta_2\),
- high self-awareness operator \(\mathcal{O}_\mathrm{self}(\Psi) \ge \phi_\mathrm{self}\).

This filters out low-level imitation and is used in transfer considerations
(`04_TRANSFER_CYCLE_en.md`).

---

## 5. Practical estimation

For data-driven systems we use observable proxies:

\[
\widehat{A}(\Psi)
= w_1 \widehat{R}(\Psi)
+ w_2 \widehat{D}(\Psi)
+ w_3 \widehat{I}(\Psi),
\]

where \(\widehat{R}, \widehat{D}, \widehat{I}\) are estimators built on features
\(x_\Psi = \phi(\mathcal{D}(\Psi))\) (see `06_QMPT_OBSERVABLES_en.md`).

---

## 6. Summary

- \(A(\Psi)\) aggregates rarity, structural distance and impact.
- Thresholds \(\theta_1, \theta_2\) separate rare patterns from full anomalies.
- Upgrade anomalies additionally raise layer capacity.
- Self-recognizing anomalies also satisfy high \(\mathcal{O}_\mathrm{self}\).
- Observable estimators \(\widehat{A}\) enable practical measurement and testing.
