"""
Interconnection-limit scenario (exploratory, beyond the base exercise): what if the
point-of-interconnection (POI) export cap is 150 MW, tighter than the 250 MW inverter
limit already modeled in the main Q2 analysis?

Today's base case barely clips solar (372 MWh/year) because the only constraint is the
300 MW-DC / 250 MW-AC inverter ratio, and panel output rarely exceeds 250 MW. A binding
150 MW POI limit is a much more realistic story for many interconnection-constrained NYC
projects, and it should make storage's role -- absorbing otherwise-curtailed solar instead
of letting it spill -- much more valuable, since there is now a large pool of curtailed
energy for storage to capture instead of a negligible one.

Run from the repo root: `<venv>/bin/python3 interconnection_scenario/interconnection_analysis.py`
Requires scipy (for the combined-system per-day LP).

Modeling:
  Standalone Solar (no storage) - delivered_t = min(shape_t * 300 MW, 250 MW inverter,
    150 MW POI). Since 150 < 250, the POI is now the binding constraint whenever panel
    output exceeds 150 MW; interconnection-clipped energy = available_solar_t - delivered_t.

  Standalone Storage - unaffected. Storage's own 50 MW max is well under the 150 MW POI
    cap, so it never binds; identical to the main Q2b LP result.

  Combined Solar + Storage - solar and storage discharge SHARE the 150 MW POI:
    solar_export_t + discharge_t <= 150 MW
  Storage can charge for $0 from whatever solar is curtailed at the POI (available solar
  minus what's exported), up to the smaller of that curtailed amount or its own 50 MW
  charge limit, before paying the grid price for any remaining charging need -- the same
  free-first priority as the main Q2c model, just now drawing from a much larger pool of
  curtailed energy.
"""
import csv
import numpy as np
from datetime import datetime
from collections import defaultdict
from scipy.optimize import linprog

rows = []
with open('hourly_data.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.strptime(row['weather year EST hour beginning'], '%Y-%m-%d %H:%M:%S')
        rows.append({
            'ts': ts,
            'shape': float(row['Solar Shape (Normalized)']),
            'price': float(row['NYISO (NYC Zone) Historical Day Ahead Energy Price ($/MWh)']),
        })

SOLAR_MW, INV_MW = 300, 250
STOR_MW, STOR_MWH = 50, 200
POI_MW = 150  # interconnection limit, tighter than the 250 MW inverter limit

# Baseline (no POI limit / today's 250 MW inverter-only case), from the main Q2 analysis
BASELINE = {
    'solar': 18_803_819,
    'storage': 1_977_954,
    'combined': 20_791_797,
}

by_day = defaultdict(list)
for row in rows:
    by_day[row['ts'].date()].append(row)

# ---------- Standalone Solar under the 150 MW POI limit ----------
solar_150_revenue = 0.0
solar_150_delivered = 0.0
solar_150_clipped = 0.0
for row in rows:
    available = min(row['shape'] * SOLAR_MW, INV_MW)
    delivered = min(available, POI_MW)
    solar_150_delivered += delivered
    solar_150_clipped += available - delivered
    solar_150_revenue += delivered * row['price']


def optimize_combined_day_with_poi(prices, available_solar):
    """Variables per hour: solar_export, c_free, c_grid, discharge (4 vars/hour)."""
    n = len(prices)
    prices = np.array(prices)
    available_solar = np.array(available_solar)
    # objective: minimize (c_grid cost) - (solar_export revenue) - (discharge revenue)
    c_obj = np.concatenate([-prices, np.zeros(n), prices, -prices])
    A_ub, b_ub = [], []

    def block(var_idx_ranges, coefs_per_range):
        row = np.zeros(4 * n)
        for (start, t), coef in zip(var_idx_ranges, coefs_per_range):
            row[start:start + t] = coef
        return row

    # SOC bounds at every hour t: 0 <= sum_{h<=t}(c_free+c_grid-discharge) <= 200
    for t in range(1, n + 1):
        upper = np.zeros(4 * n)
        upper[n:n + t] = 1.0          # c_free
        upper[2 * n:2 * n + t] = 1.0  # c_grid
        upper[3 * n:3 * n + t] = -1.0  # -discharge
        A_ub.append(upper); b_ub.append(STOR_MWH)
        A_ub.append(-upper); b_ub.append(0.0)

    for t in range(n):
        # charger power cap: c_free_t + c_grid_t <= 50
        row = np.zeros(4 * n)
        row[n + t] = 1.0
        row[2 * n + t] = 1.0
        A_ub.append(row); b_ub.append(STOR_MW)

        # free charge can't exceed what's actually curtailed at the POI:
        # c_free_t <= available_solar_t - solar_export_t  =>  solar_export_t + c_free_t <= available_solar_t
        row = np.zeros(4 * n)
        row[t] = 1.0
        row[n + t] = 1.0
        A_ub.append(row); b_ub.append(available_solar[t])

        # shared POI export cap: solar_export_t + discharge_t <= 150
        row = np.zeros(4 * n)
        row[t] = 1.0
        row[3 * n + t] = 1.0
        A_ub.append(row); b_ub.append(POI_MW)

    bounds = ([(0, available_solar[i]) for i in range(n)] +  # solar_export
              [(0, STOR_MW)] * n +                            # c_free
              [(0, STOR_MW)] * n +                            # c_grid
              [(0, STOR_MW)] * n)                              # discharge

    res = linprog(c_obj, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method='highs')
    solar_export, c_free, c_grid, discharge = (res.x[:n], res.x[n:2 * n],
                                                res.x[2 * n:3 * n], res.x[3 * n:])
    solar_rev = float(np.sum(prices * solar_export))
    storage_rev = float(np.sum(prices * discharge) - np.sum(prices * c_grid))
    return solar_export, c_free, c_grid, discharge, solar_rev, storage_rev


combined_150_solar_revenue = 0.0
combined_150_storage_revenue = 0.0
free_charged_total = 0.0
grid_charged_total = 0.0
poi_clipped_avoided = 0.0  # curtailed solar actually captured by storage (vs. spilled)

for day, day_rows in by_day.items():
    day_rows_sorted = sorted(day_rows, key=lambda x: x['ts'])
    prices = [h['price'] for h in day_rows_sorted]
    available_solar = [min(h['shape'] * SOLAR_MW, INV_MW) for h in day_rows_sorted]

    solar_export, c_free, c_grid, discharge, solar_rev, storage_rev = \
        optimize_combined_day_with_poi(prices, available_solar)

    combined_150_solar_revenue += solar_rev
    combined_150_storage_revenue += storage_rev
    free_charged_total += float(np.sum(c_free))
    grid_charged_total += float(np.sum(c_grid))

combined_150_total = combined_150_solar_revenue + combined_150_storage_revenue
standalone_150_sum = solar_150_revenue + BASELINE['storage']
interaction_150 = combined_150_total - standalone_150_sum

print('=== Standalone Solar, 150 MW POI limit ===')
print(f'Delivered energy: {solar_150_delivered:,.0f} MWh')
print(f'POI-clipped energy: {solar_150_clipped:,.0f} MWh ({100*solar_150_clipped/(solar_150_delivered+solar_150_clipped):.2f}% of inverter-available)')
print(f'Revenue: ${solar_150_revenue:,.0f} (vs. ${BASELINE["solar"]:,.0f} with no POI limit)')
print()

print('=== Standalone Storage (unaffected by the POI limit) ===')
print(f'Revenue: ${BASELINE["storage"]:,.0f}')
print()

print('=== Combined Solar + Storage, 150 MW shared POI limit ===')
print(f'Solar export revenue: ${combined_150_solar_revenue:,.0f}')
print(f'Storage revenue: ${combined_150_storage_revenue:,.0f}')
print(f'  free (POI-curtailed-solar) charging used: {free_charged_total:,.0f} MWh')
print(f'  grid charging used: {grid_charged_total:,.0f} MWh')
print(f'Combined total: ${combined_150_total:,.0f}')
print()

print('=== Interaction Benefit Comparison ===')
print(f'Sum of standalone (150 MW POI): ${standalone_150_sum:,.0f}')
print(f'Combined total (150 MW POI): ${combined_150_total:,.0f}')
print(f'Interaction benefit: ${interaction_150:,.0f} ({100*interaction_150/standalone_150_sum:.2f}%)')
print()
baseline_standalone_sum = BASELINE['solar'] + BASELINE['storage']
baseline_interaction = BASELINE['combined'] - baseline_standalone_sum
print(f'(For reference, no-POI-limit base case interaction benefit: '
      f'${baseline_interaction:,.0f}, {100*baseline_interaction/baseline_standalone_sum:.4f}%)')
