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

## Caveats

- Illustrative: a real interconnection study would need actual POI capacity, not an assumed
  150 MW round number.
- Same zero-degradation/zero-cycling-cost and perfect-price-foresight simplifications as the
  main analysis apply here too — see the main analysis's caveats for detail.
- This scenario is intentionally kept separate from `../analysis/` and the main deck, since
  it changes a structural assumption (interconnection capacity) rather than extending the
  base exercise's methodology.

## Files

- `interconnection_analysis.py` — the LP-based revenue computation (requires `scipy`; run
  from the repo root: `python3 interconnection_scenario/interconnection_analysis.py`)
- `interconnection_chart.py` — generates the comparison chart
- `interconnection_interaction_benefit.png` — output chart
