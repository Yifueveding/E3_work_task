# Interconnection-Limit Scenario (Exploratory, Beyond the Base Exercise)

**Question:** the base Q2 analysis (`../analysis/`) finds a negligible interaction benefit
(+0.05%) from pairing solar and storage, because the only constraint on solar export is the
300 MW-DC / 250 MW-AC inverter ratio, which clips almost nothing (372 MWh/year — 0.07% of
gross generation). What if there's also a binding **point-of-interconnection (POI) export
limit**, tighter than the inverter itself? That's a common real-world constraint for
interconnection-limited NYC projects, and it should make storage's ability to absorb
otherwise-curtailed solar much more valuable.

**Assumption used here:** a 150 MW POI limit (vs. today's 250 MW inverter limit).

## Methodology

- **Standalone Solar:** delivered = min(shape × 300 MW, 250 MW inverter, 150 MW POI). Since
  150 < 250, the POI is now the binding constraint whenever panel output exceeds 150 MW.
- **Standalone Storage:** unaffected — storage's own 50 MW max is well under the 150 MW POI
  cap, so it never binds. Identical to the main Q2b LP result.
- **Combined Solar + Storage:** solar export and storage discharge now **share** the 150 MW
  POI (`solar_export_t + discharge_t ≤ 150 MW` every hour). Storage can charge for $0 from
  whatever solar is curtailed at the POI (available solar minus what's exported), up to its
  own 50 MW charge limit, before paying the grid price for any remaining charging need — the
  same free-first priority as the main Q2c model, just now drawing from a much larger pool
  of curtailed energy. Solved as a per-day linear program (see `interconnection_analysis.py`),
  consistent with the multi-cycle LP approach used in the main analysis.

Uses the same 2023 NYISO N.Y.C. day-ahead price data and the same $405M/$75M/$445M capex
figures as the main analysis (not re-run here since capex doesn't depend on the POI limit).

## Results

| | No POI Limit (base case) | 150 MW POI Limit |
|---|---|---|
| Standalone Solar revenue | $18.80M | **$15.70M** (17.75% of inverter-available energy now clipped, vs. 0.07% before) |
| Standalone Storage revenue | $1.98M | $1.98M (unaffected) |
| Sum of standalone | $20.78M | $17.68M |
| Combined total | $20.79M | **$19.04M** |
| **Interaction benefit** | **+$10,024 (+0.05%)** | **+$1,363,247 (+7.71%)** |

See `interconnection_interaction_benefit.png`.

## Why the benefit grows so much

With a 150 MW POI limit, standalone solar alone wastes **97,870 MWh/year** (17.75% of what
the inverter would otherwise allow) — a huge pool of otherwise-curtailed energy. In the
combined system, storage captures **81,594 MWh** of that for free (plus 78,114 MWh of
grid-charged energy) instead of letting it spill, and resells it at better hours. That's the
real mechanism the base case's 0.07%-clipping world could never demonstrate.

One nuance: combined solar export revenue ($14.70M) is actually *lower* than standalone
solar's POI-limited revenue ($15.70M), because storage discharge sometimes competes with
solar for the same 150 MW export slot. This is more than offset by storage's much larger
revenue in the combined case ($4.34M vs. $1.98M standalone) — the LP resolves this
solar-vs-storage export tradeoff endogenously in favor of the higher-value option each hour.

## Reserve (Headroom/Footroom) Scenario Under the POI Limit

The main analysis also layers an illustrative NYISO reserve scenario on top of energy
revenue (`../analysis/q2_reserve_scenario.py`, at $1.25/MW-hr). Extending that here reveals
a genuine tension: **the same POI constraint that makes the energy interaction benefit much
larger also makes storage's reserve contribution smaller.**

- **Footroom** (down-reserve, i.e. ability to charge more) is unaffected by the POI, since
  charging draws from the grid rather than competing for export capacity.
- **Headroom** (up-reserve, i.e. ability to discharge more) now shares the 150 MW POI with
  solar: `headroom_t = min(50 MW − discharge_t, 150 MW − solar_export_t − discharge_t)`.
  During the 590 hours/year where solar's own export already claims most of the 150 MW,
  storage's usable headroom drops well below its 50 MW nameplate.
- Storage also ends up dispatching (charging or discharging) across *more* hours than in the
  base case, since it now has a much larger pool of curtailed solar to charge from and must
  spread discharge to fit within the shared POI — leaving fewer purely idle hours available
  to offer the double-sided (headroom + footroom) reserve product.

| | No POI Limit (base case) | 150 MW POI Limit |
|---|---|---|
| Standalone Storage reserve | $781,375 | $781,375 (unaffected) |
| Combined headroom offered | 312,550 MWh | **106,110 MWh** |
| Combined footroom offered | 312,950 MWh | 289,750 MWh |
| **Combined reserve revenue** | **$781,875** | **$494,824** (−36.7%) |
| Combined energy + reserve total | $21,573,672 | $19,537,241 |

See `interconnection_reserve_scenario.py` and `interconnection_reserve_tradeoff.png`. In short: don't assume a scenario that's good for
one revenue stream (energy arbitrage) is automatically good for another (reserve) — here
they move in opposite directions, because both draw on the same underlying physical
resource (the storage's power rating and the shared export capacity).

## Caveats

- Illustrative: a real interconnection study would need actual POI capacity, not an assumed
  150 MW round number.
- Same zero-degradation/zero-cycling-cost and perfect-price-foresight simplifications as the
  main analysis apply here too — see the main analysis's caveats for detail.
- This scenario is intentionally kept separate from `../analysis/` and the main deck, since
  it changes a structural assumption (interconnection capacity) rather than extending the
  base exercise's methodology.

## Files

- `interconnection_analysis.py` — the LP-based energy revenue computation (requires
  `scipy`; run from the repo root: `python3 interconnection_scenario/interconnection_analysis.py`)
- `interconnection_reserve_scenario.py` — the reserve (headroom/footroom) computation under
  the POI limit (requires `scipy`)
- `interconnection_reserve_tradeoff_chart.py` — generates the energy-vs-reserve tradeoff chart
- `interconnection_reserve_tradeoff.png` — output chart
- `interconnection_chart.py` — generates the energy interaction-benefit comparison chart
- `interconnection_interaction_benefit.png` — output chart
- `q2_energy_only_chart_interconnection.py` — same style as `analysis/q2_energy_only_by_config.png`,
  using the 150 MW POI scenario's numbers
- `q2_energy_only_by_config_interconnection.png` — output chart
- `q2_energy_plus_reserve_chart_interconnection.py` — same style as
  `analysis/q2_energy_plus_reserve_by_config.png`, stacking reserve on top of energy revenue
  under the 150 MW POI scenario; shares the same y-axis scale as the energy-only chart above
- `q2_energy_plus_reserve_by_config_interconnection.png` — output chart
