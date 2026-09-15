# Scenario Comparison: Energy-only vs. Interconnection-limit vs. Energy + Reserve

**Question:** across the three structural scenarios explored in this repo (today's 250 MW
inverter-only case, a tighter 150 MW point-of-interconnection limit, and an illustrative
NYISO reserve add-on), how do Standalone Solar, Standalone Battery, and Combined Solar +
Storage compare on annual revenue, per-unit energy value, and payback?

**Assumption used here:** all three scenarios share the same 2023 NYISO N.Y.C. day-ahead
price data, the same $405M / $75M / $445M capex figures (solar / storage / combined —
package pricing on the combined system, not a simple sum of standalone capex), and the
same per-day LP dispatch formulation (`OPTIMIZATION_MODEL.md`). Only the structural
constraint or revenue stream being tested changes across scenarios.

## Methodology

- **Energy-only** (`analysis/`) — today's base case: solar capped by the 300 MW-DC / 250
  MW-AC inverter ratio (negligible clipping, 0.07%/yr); storage dispatched by a per-day LP
  multi-cycle energy-arbitrage optimum; combined system lets storage charge for free from
  otherwise-clipped solar. See `analysis/q2.tex`.
- **Interconnection-limit** (`interconnection_scenario/`) — same dispatch logic, but with
  a binding 150 MW point-of-interconnection export cap (tighter than the 250 MW inverter),
  so solar export competes with storage discharge for the shared POI, and storage has a
  much larger pool of otherwise-curtailed solar to absorb for free. See
  `interconnection_scenario/README.md`.
- **Energy + Reserve** (`analysis/q2_reserve_scenario.py`) — layers an illustrative NYISO
  operating reserve (headroom/footroom) revenue stream on top of the energy-only dispatch,
  at $1.25/MW-hr (midpoint of the $1–1.5/MW range). Solar cannot offer reserve (variable,
  non-dispatchable); storage's headroom/footroom is classified hour-by-hour from its actual
  LP dispatch solution.
- **Per-unit Energy Value** = annual revenue ÷ MWh actually delivered/discharged that
  scenario (solar delivered energy; storage discharge; combined = solar + storage
  discharge). Under Energy + Reserve, total (energy + reserve) revenue is divided by the
  same *energy* MWh, since reserve is a capacity product, not delivered energy.
- **Pay-back Period** is the discounted-NPV crossing year (matches `analysis/npv_chart.py`):
  year cumulative NPV first turns non-negative, with NPV(t) = −Capex + Σ Revenue/(1.02)^i —
  i.e. a 2% discount rate, flat nominal revenue, no O&M/tax/financing/escalation. (Storage's
  energy-only crossing year, 72, is found by extending `npv_chart.py`'s 40-year plotting
  horizon — well past a real battery's useful life without augmentation; treat it as
  illustrating discount-rate sensitivity, not a realistic recommendation.)

## Results

### Energy-only (base case, 250 MW inverter limit)

| | Standalone Solar | Standalone Battery | Combined Solar and Storage |
|---|---|---|---|
| Annual Revenue ($M) | 18.80 | 1.98 | 20.79 |
| Per-unit Energy Value ($/MWh) | 34.10 | 15.77 | 30.69 |
| Pay-back Period (years) | 29 | 72 | 29 |

### Interconnection-limit (150 MW POI)

| | Standalone Solar | Standalone Battery | Combined Solar and Storage |
|---|---|---|---|
| Annual Revenue ($M) | 15.70 | 1.98 | 19.04 |
| Per-unit Energy Value ($/MWh) | 34.62 | 15.77 | 32.49 |
| Pay-back Period (years) | 37 | 72 | 32 |

### Energy + Reserve ($1.25/MW-hr headroom/footroom, no POI limit)

| | Standalone Solar | Standalone Battery | Combined Solar and Storage |
|---|---|---|---|
| Annual Revenue ($M) | 18.80 | 2.76 | 21.57 |
| Per-unit Energy Value ($/MWh) | 34.10 | 22.00 | 31.85 |
| Pay-back Period (years) | 29 | 40 | 27 |

See `analysis/configuration_summary.csv` for the same figures in tidy (long) format.

## Why the scenarios move the way they do

The interconnection limit hurts standalone solar (revenue −16.5%, since 17.75% of
inverter-available energy is now POI-clipped) but helps the combined system relatively:
storage captures much more of that otherwise-wasted energy for free, so combined revenue
falls only −8.4% versus solar's −16.5% — the interaction benefit between solar and storage
grows from +0.05% (energy-only) to +7.71% (interconnection-limit). Reserve revenue moves in
the opposite direction: storage is the only source of reserve value (+39.5% on a standalone
basis, +3.76% combined), since solar cannot commit firm capacity to a reserve product.
Combined Solar + Storage is the best (or tied-best) payback in every scenario; Standalone
Battery is consistently the weakest, though reserve revenue meaningfully closes that gap
(72 → 40 years) while the POI limit widens it further (72 years either way, since storage's
own 50 MW never binds against a 150 MW cap — it's solar and the combined system that get
squeezed).

## Caveats

- Energy-only and Energy + Reserve share the same (no-POI) dispatch; Interconnection-limit
  is intentionally kept structurally separate, since it changes a physical assumption
  (export capacity) rather than adding a revenue stream — the two axes have not been
  combined (e.g. no "Interconnection-limit + Reserve" scenario here).
- Same zero-degradation, zero-cycling-cost, and perfect day-ahead-price-foresight
  simplifications apply across all three scenarios — see `analysis/q2.tex` and
  `interconnection_scenario/README.md` for detail.
- Illustrative reserve and POI figures ($1.25/MW-hr, 150 MW) are stated assumptions, not
  given exercise inputs.
- Discounted payback assumes a 2% discount rate (see `analysis/npv_chart.py` for the
  breakeven-rate sensitivity — at a more typical 4–7% utility WACC, standalone storage
  never reaches positive NPV within any reasonable horizon).

## Files

- `analysis/q2.tex`, `analysis/q2_revenue.py` — Energy-only base case
- `analysis/q2_reserve_scenario.py` — Energy + Reserve
- `interconnection_scenario/interconnection_analysis.py`,
  `interconnection_scenario/README.md` — Interconnection-limit
- `analysis/npv_chart.py`, `analysis/npv_by_config.png` — discounted payback / NPV crossing
  years underlying the Pay-back Period rows above
- `analysis/configuration_summary.csv` — all figures above in tidy (long) CSV format
