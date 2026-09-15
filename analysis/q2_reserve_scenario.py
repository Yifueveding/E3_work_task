"""
Q2d (extension, beyond the base exercise): NYISO operating reserve (headroom/footroom)
scenario. Estimates additional revenue from offering reserve capacity on top of the
energy-only backcast in q2_revenue.py, at an assumed reserve price of $1.25/MW-hr
(midpoint of the $1-1.5/MW range).

Requires scipy (same per-day LP dispatch as q2_revenue.py, so that the charge/discharge/
idle classification used for headroom/footroom matches the multi-cycle-optimized base
case rather than the old fixed 4-hour heuristic).

Headroom = capacity available to INCREASE output on call (up-reserve).
Footroom = capacity available to DECREASE output on call (down-reserve).

Assumptions (nameplate-based, state-dependent — see chat for alternatives considered):
  Solar   - cannot provide reserve. It is a variable, weather-dependent resource with no
            firm/dispatchable capacity commitment, so it does not qualify to offer NYISO
            reserve products; standalone solar earns $0 reserve revenue.
  Storage - classified hour-by-hour from the actual LP dispatch solution (not a fixed
            4-hour/4-hour/16-hour split): an hour where the LP charges (and doesn't
            discharge) offers 50 MW of footroom only; an hour where it discharges (and
            doesn't charge) offers 50 MW of headroom only; an hour where it does neither
            (idle) offers the full 50 MW of both headroom and footroom simultaneously.
            Because multi-cycle dispatch uses more charge/discharge hours and leaves fewer
            hours idle than the old single-cycle heuristic, this base case actually offers
            *less* total reserve capacity than the heuristic did.
  Combined - all reserve capacity comes from the storage component only (identical
            classification logic applied to the combined dispatch, which also has free
            clipped-solar charging); the solar component still cannot offer reserve.
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
RESERVE_PRICE = 1.25  # $/MW-hr, midpoint of the $1-1.5/MW NYISO reserve range

# Energy-only 2023 backcast revenue, multi-cycle LP dispatch, day-ahead price basis (from q2_revenue.py)
ENERGY_REVENUE = {
    'solar': 18_803_819,
    'storage': 1_977_954,
    'combined': 20_791_797,
}

by_day = defaultdict(list)
for row in rows:
    by_day[row['ts'].date()].append(row)


def optimize_standalone_day(prices):
    n = len(prices)
    prices = np.array(prices)
    c_obj = np.concatenate([prices, -prices])
    A_ub, b_ub = [], []
    for t in range(1, n + 1):
        upper = np.zeros(2 * n)
        upper[:t] = 1.0
        upper[n:n + t] = -1.0
        A_ub.append(upper); b_ub.append(STOR_MWH)
        A_ub.append(-upper); b_ub.append(0.0)
    bounds = [(0, STOR_MW)] * (2 * n)
    res = linprog(c_obj, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method='highs')
    return res.x[:n], res.x[n:]


def optimize_combined_day(prices, clip_mw):
    n = len(prices)
    prices = np.array(prices)
    free_cap = np.minimum(np.array(clip_mw), STOR_MW)
    c_obj = np.concatenate([np.zeros(n), prices, -prices])
    A_ub, b_ub = [], []
    for t in range(1, n + 1):
        upper = np.zeros(3 * n)
        upper[:t] = 1.0
        upper[n:n + t] = 1.0
        upper[2 * n:2 * n + t] = -1.0
        A_ub.append(upper); b_ub.append(STOR_MWH)
        A_ub.append(-upper); b_ub.append(0.0)
    for t in range(n):
        row = np.zeros(3 * n)
        row[t] = 1.0
        row[n + t] = 1.0
        A_ub.append(row); b_ub.append(STOR_MW)
    bounds = [(0, free_cap[i]) for i in range(n)] + [(0, STOR_MW)] * n + [(0, STOR_MW)] * n
    res = linprog(c_obj, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method='highs')
    c_free, c_grid = res.x[:n], res.x[n:2 * n]
    return c_free + c_grid, res.x[2 * n:]


def classify_reserve(charge, discharge):
    headroom = footroom = 0.0
    for c, d in zip(charge, discharge):
        is_charge, is_discharge = c > 0.5, d > 0.5
        if is_charge and not is_discharge:
            footroom += STOR_MW
        elif is_discharge and not is_charge:
            headroom += STOR_MW
        else:  # idle (or, rarely, a fractional tie) offers both directions
            headroom += STOR_MW
            footroom += STOR_MW
    return headroom, footroom


standalone_headroom = standalone_footroom = 0.0
combined_headroom = combined_footroom = 0.0

for day, day_rows in by_day.items():
    day_rows_sorted = sorted(day_rows, key=lambda x: x['ts'])
    prices = [h['price'] for h in day_rows_sorted]

    c, d = optimize_standalone_day(prices)
    h, f = classify_reserve(c, d)
    standalone_headroom += h; standalone_footroom += f

    clip_mw = [max(0.0, r['shape'] * SOLAR_MW - INV_MW) for r in day_rows_sorted]
    c2, d2 = optimize_combined_day(prices, clip_mw)
    h2, f2 = classify_reserve(c2, d2)
    combined_headroom += h2; combined_footroom += f2

standalone_reserve_mwh = standalone_headroom + standalone_footroom
combined_reserve_mwh = combined_headroom + combined_footroom

storage_reserve_revenue = standalone_reserve_mwh * RESERVE_PRICE
combined_reserve_revenue = combined_reserve_mwh * RESERVE_PRICE
solar_reserve_revenue = 0.0  # solar cannot provide reserve

print(f'Reserve price assumed: ${RESERVE_PRICE:.2f}/MW-hr')
print()

print('=== Standalone Solar ===')
print('Solar cannot provide reserve (variable, non-dispatchable resource).')
print(f'Reserve revenue: ${solar_reserve_revenue:,.0f}')
print(f'Energy-only revenue: ${ENERGY_REVENUE["solar"]:,.0f}')
print(f'Energy + reserve revenue: ${ENERGY_REVENUE["solar"] + solar_reserve_revenue:,.0f}')
print()

print('=== Standalone Storage ===')
print(f'Headroom offered: {standalone_headroom:,.0f} MW-hr/yr')
print(f'Footroom offered: {standalone_footroom:,.0f} MW-hr/yr')
print(f'Reserve revenue: ${storage_reserve_revenue:,.0f}')
print(f'Energy-only revenue: ${ENERGY_REVENUE["storage"]:,.0f}')
print(f'Energy + reserve revenue: ${ENERGY_REVENUE["storage"] + storage_reserve_revenue:,.0f}')
print(f'Reserve uplift: {100*storage_reserve_revenue/ENERGY_REVENUE["storage"]:.2f}%')
print()

print('=== Combined Solar + Storage ===')
print('Reserve revenue comes entirely from the storage component (solar cannot provide reserve).')
print(f'Headroom offered: {combined_headroom:,.0f} MW-hr/yr')
print(f'Footroom offered: {combined_footroom:,.0f} MW-hr/yr')
print(f'Reserve revenue: ${combined_reserve_revenue:,.0f}')
print(f'Energy-only revenue: ${ENERGY_REVENUE["combined"]:,.0f}')
print(f'Energy + reserve revenue: ${ENERGY_REVENUE["combined"] + combined_reserve_revenue:,.0f}')
print(f'Reserve uplift: {100*combined_reserve_revenue/ENERGY_REVENUE["combined"]:.2f}%')
