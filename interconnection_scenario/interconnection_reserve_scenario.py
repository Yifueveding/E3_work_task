"""
Reserve (headroom/footroom) scenario under the 150 MW interconnection limit, extending
interconnection_analysis.py the same way analysis/q2_reserve_scenario.py extends the base
Q2b/Q2c model.

Key difference from the base-case reserve scenario: storage's HEADROOM (up-reserve, i.e.
ability to increase export on call) is no longer capped only by its own 50 MW power rating
-- it now shares the 150 MW point-of-interconnection (POI) with solar, so headroom is also
capped by whatever POI capacity remains after solar's current export:

    headroom_t = min(50 MW - discharge_t, 150 MW - solar_export_t - discharge_t)

FOOTROOM (down-reserve, i.e. ability to charge more / discharge less) is unaffected by the
POI limit, since charging draws power from the grid rather than competing for export
capacity -- footroom_t = 50 MW whenever storage isn't already charging at full power,
exactly as in the base-case model.

Standalone storage's reserve figure is unaffected by the interconnection limit (its own
50 MW max is well under the 150 MW POI, so it never binds) -- identical to the base case.
Standalone solar still cannot provide reserve at all ($0).

Run from the repo root: `<venv>/bin/python3 interconnection_scenario/interconnection_reserve_scenario.py`
Requires scipy.
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
POI_MW = 150
RESERVE_PRICE = 1.25

# From interconnection_analysis.py / the main analysis (unaffected pieces)
STANDALONE_STORAGE_RESERVE = 781_375  # unchanged: 50 MW << 150 MW POI, never binds
COMBINED_150_ENERGY_TOTAL = 19_042_417

by_day = defaultdict(list)
for row in rows:
    by_day[row['ts'].date()].append(row)


def optimize_combined_day_with_poi(prices, available_solar):
    n = len(prices)
    prices = np.array(prices)
    available_solar = np.array(available_solar)
    c_obj = np.concatenate([-prices, np.zeros(n), prices, -prices])
    A_ub, b_ub = [], []
    for t in range(1, n + 1):
        upper = np.zeros(4 * n)
        upper[n:n + t] = 1.0
        upper[2 * n:2 * n + t] = 1.0
        upper[3 * n:3 * n + t] = -1.0
        A_ub.append(upper); b_ub.append(STOR_MWH)
        A_ub.append(-upper); b_ub.append(0.0)
    for t in range(n):
        row = np.zeros(4 * n)
        row[n + t] = 1.0
        row[2 * n + t] = 1.0
        A_ub.append(row); b_ub.append(STOR_MW)

        row = np.zeros(4 * n)
        row[t] = 1.0
        row[n + t] = 1.0
        A_ub.append(row); b_ub.append(available_solar[t])

        row = np.zeros(4 * n)
        row[t] = 1.0
        row[3 * n + t] = 1.0
        A_ub.append(row); b_ub.append(POI_MW)

    bounds = ([(0, available_solar[i]) for i in range(n)] +
              [(0, STOR_MW)] * n + [(0, STOR_MW)] * n + [(0, STOR_MW)] * n)
    res = linprog(c_obj, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method='highs')
    solar_export, c_free, c_grid, discharge = (res.x[:n], res.x[n:2 * n],
                                                res.x[2 * n:3 * n], res.x[3 * n:])
    return solar_export, c_free + c_grid, discharge


combined_headroom = 0.0
combined_footroom = 0.0
poi_bound_hours = 0  # hours where the POI limit actually reduced headroom below 50 MW

for day, day_rows in by_day.items():
    day_rows_sorted = sorted(day_rows, key=lambda x: x['ts'])
    prices = [h['price'] for h in day_rows_sorted]
    available_solar = [min(h['shape'] * SOLAR_MW, INV_MW) for h in day_rows_sorted]

    solar_export, c_total, discharge = optimize_combined_day_with_poi(prices, available_solar)

    for i in range(len(prices)):
        is_charging = c_total[i] > 0.5
        # footroom: unaffected by the POI (charging doesn't compete for export capacity)
        footroom_t = 0.0 if (discharge[i] > 0.5 and not is_charging) else STOR_MW

        # headroom: bounded by both the storage's own remaining power AND the POI's
        # remaining export capacity after solar's current export
        own_headroom = STOR_MW - discharge[i]
        poi_headroom = max(0.0, POI_MW - solar_export[i] - discharge[i])
        headroom_t = 0.0 if is_charging else min(own_headroom, poi_headroom)

        if not is_charging and poi_headroom < own_headroom - 1e-6:
            poi_bound_hours += 1

        combined_headroom += headroom_t
        combined_footroom += footroom_t

combined_reserve_revenue = (combined_headroom + combined_footroom) * RESERVE_PRICE
combined_total_with_reserve = COMBINED_150_ENERGY_TOTAL + combined_reserve_revenue

print('=== Standalone Solar (150 MW POI) ===')
print('Still cannot provide reserve: $0')
print()

print('=== Standalone Storage (unaffected by the POI limit) ===')
print(f'Reserve revenue: ${STANDALONE_STORAGE_RESERVE:,.0f} (identical to the base case; 50 MW << 150 MW POI never binds)')
print()

print('=== Combined Solar + Storage, 150 MW shared POI ===')
print(f'Headroom offered: {combined_headroom:,.0f} MW-hr/yr')
print(f'Footroom offered: {combined_footroom:,.0f} MW-hr/yr')
print(f'Hours where the POI limit actually reduced headroom below 50 MW: {poi_bound_hours:,}')
print(f'Reserve revenue: ${combined_reserve_revenue:,.0f}')
print(f'Energy-only total (from interconnection_analysis.py): ${COMBINED_150_ENERGY_TOTAL:,.0f}')
print(f'Energy + reserve total: ${combined_total_with_reserve:,.0f}')
print()

print('=== For reference: base case (no POI limit) combined reserve ===')
print('Combined reserve revenue: $781,875 (from analysis/q2_reserve_scenario.py)')
