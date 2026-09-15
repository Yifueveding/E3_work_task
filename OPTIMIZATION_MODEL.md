# Storage Dispatch Optimization Model

This document specifies the per-day linear program (LP) used throughout this repository
to dispatch the battery storage system, in its three variants. The LP is free to discover
multiple charge/discharge cycles within a day when prices oscillate enough to make it
profitable (see `analysis/q2.tex`, Q2b, for the multi-cycle dispatch detail).

Each day is solved independently (365 LPs per year), using
[`scipy.optimize.linprog`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)
with `method='highs'`.

## Notation

| Symbol | Meaning |
|---|---|
| $d$ | A single day (24 hours, except DST transition days: 23 or 25) |
| $h \in d$ | An hour within day $d$ |
| $p_h$ | Day-ahead energy price that hour ($/MWh) |
| $s_h$ | Normalized solar production shape that hour |
| $A_h$ | Available (inverter-capped) solar output that hour: $\min(s_h \times 300,\ 250)$ MW |
| $C_h$ | Clipped/curtailed solar that hour: $\max(s_h \times 300 - 250,\ 0)$ MW |
| $P^{\max}$ | Storage power rating = 50 MW |
| $E^{\max}$ | Storage energy capacity = 200 MWh |
| POI | Point-of-interconnection export limit (150 MW, interconnection scenario only) |

Round-trip efficiency is 100% (per the given input), so charge/discharge have no loss
term. State of charge (SOC) starts each day at 0.

---

## Model 1 — Standalone Storage

**Implementation:** `analysis/q2_revenue.py`, function `optimize_standalone_day`.

**Decision variables** (per hour $h \in d$):
- $c_h \geq 0$ — charge rate (MW)
- $g_h \geq 0$ — discharge rate (MW)

**Objective** — maximize net energy revenue for the day:

$$\max \sum_{h \in d} p_h \,(g_h - c_h)$$

**Constraints:**

$$0 \leq c_h \leq P^{\max}, \qquad 0 \leq g_h \leq P^{\max} \qquad \forall h \in d$$

$$0 \ \leq\ \underbrace{\sum_{h' \leq h,\ h' \in d} (c_{h'} - g_{h'})}_{\text{SOC at end of hour } h} \ \leq\ E^{\max} \qquad \forall h \in d$$

The SOC constraint is what lets the optimizer find multiple cycles: it only bounds the
*running total*, not the number of charge/discharge switches, so any sequence of
charge/discharge decisions that keeps SOC within $[0, E^{\max}]$ at every hour is feasible.

**In code**, the cumulative SOC constraint is built as a triangular coefficient matrix
(one row per hour $h$, with 1's for $c_{h'}$ and $-1$'s for $g_{h'}$ over all $h' \leq h$),
passed to `linprog` as `A_ub`/`b_ub` — once for the upper bound ($\leq E^{\max}$) and once
negated for the lower bound ($\geq 0$).

---

## Model 2 — Combined Solar + Storage (free clipped-solar charging)

**Implementation:** `analysis/q2_revenue.py`, function `optimize_combined_day`.

Solar export itself is *not* a decision variable here — solar always delivers everything
up to $A_h$ and that revenue is computed separately (it doesn't compete with storage for
anything in this variant; see Model 3 for the version where it does). Storage's charging
is split into a free portion (sourced from otherwise-curtailed solar) and a grid-priced
portion:

**Decision variables** (per hour $h \in d$):
- $f_h \geq 0$ — charge sourced from clipped solar (\$0 cost)
- $z_h \geq 0$ — charge sourced from the grid (price $p_h$)
- $g_h \geq 0$ — discharge rate (MW)

**Objective:**

$$\max \sum_{h \in d} \big[\, p_h\, g_h \;-\; p_h\, z_h \,\big]$$

($f_h$ carries a zero cost coefficient — the optimizer naturally prefers it over $z_h$
since it strictly lowers cost, with no need for an explicit priority constraint.)

**Constraints:**

$$0 \leq f_h \leq \min(C_h,\ P^{\max}), \qquad 0 \leq z_h \leq P^{\max}, \qquad 0 \leq g_h \leq P^{\max}$$

$$f_h + z_h \leq P^{\max} \qquad \text{(charger power cap — free + grid charging share the same 50 MW limit)}$$

$$0 \ \leq\ \sum_{h' \leq h,\ h' \in d} \big[(f_{h'} + z_{h'}) - g_{h'}\big] \ \leq\ E^{\max} \qquad \forall h \in d$$

---

## Model 3 — Interconnection-Limited Combined System

**Implementation:** `interconnection_scenario/interconnection_analysis.py`, function
`optimize_combined_day_with_poi`.

Here solar and storage **share** a single point-of-interconnection (POI) export limit
(150 MW), tighter than the 250 MW inverter limit — so solar export itself becomes a
decision variable, since exporting more solar in an hour can crowd out storage discharge
(or vice versa).

**Decision variables** (per hour $h \in d$):
- $x_h \geq 0$ — solar exported (MW), $x_h \leq A_h$
- $f_h \geq 0$ — storage charge sourced from curtailed solar (\$0 cost)
- $z_h \geq 0$ — storage charge sourced from the grid
- $g_h \geq 0$ — storage discharge rate (MW)

**Objective:**

$$\max \sum_{h \in d} \big[\, p_h\, x_h \;+\; p_h\, g_h \;-\; p_h\, z_h \,\big]$$

**Constraints:**

$$0 \leq x_h \leq A_h$$

$$f_h \leq A_h - x_h \qquad \text{(free charge can't exceed what's actually curtailed at the POI)}$$

$$f_h + z_h \leq P^{\max}, \qquad 0 \leq z_h,\, g_h \leq P^{\max}$$

$$x_h + g_h \ \leq\ \text{POI} \qquad \text{(shared export cap — the key new constraint)}$$

$$0 \ \leq\ \sum_{h' \leq h,\ h' \in d} \big[(f_{h'} + z_{h'}) - g_{h'}\big] \ \leq\ E^{\max} \qquad \forall h \in d$$

This is the constraint that produces the finding in
`interconnection_scenario/README.md`: because $x_h$ and $g_h$ now compete for the same 150
MW, storage's discharge sometimes crowds out solar export (and vice versa) — the LP
resolves that tradeoff endogenously in favor of whichever earns more that hour, rather
than through any hand-coded priority rule.

---

## Reserve (headroom/footroom) classification

The illustrative NYISO reserve scenarios (`analysis/q2_reserve_scenario.py`,
`interconnection_scenario/interconnection_reserve_scenario.py`) are **not** part of the
optimization itself — they're a post-hoc classification of each hour's LP solution:

- An hour where the LP charges (and doesn't discharge) offers $P^{\max}$ of **footroom**
  only (down-reserve capacity).
- An hour where it discharges (and doesn't charge) offers $P^{\max}$ of **headroom** only
  (up-reserve capacity) — in the interconnection-limited variant, this is further capped
  by remaining POI room: $\text{headroom}_h = \min(P^{\max} - g_h,\ \text{POI} - x_h - g_h)$.
- An idle hour offers the full $P^{\max}$ of *both* simultaneously.

Reserve revenue is then $\$1.25 \times \sum_h (\text{headroom}_h + \text{footroom}_h)$.

## Solving it

All three models are small enough (at most $4n$ variables and $\sim 3n$ constraints for
$n \leq 25$ hours) to solve in well under a second per day; solving all 365 days of a
year takes a few seconds total. Requires `scipy` — none of these scripts run under the
plain system Python used elsewhere in this repo:

```bash
<venv-with-scipy>/bin/python3 analysis/q2_revenue.py
<venv-with-scipy>/bin/python3 analysis/q2_reserve_scenario.py
<venv-with-scipy>/bin/python3 interconnection_scenario/interconnection_analysis.py
<venv-with-scipy>/bin/python3 interconnection_scenario/interconnection_reserve_scenario.py
```
