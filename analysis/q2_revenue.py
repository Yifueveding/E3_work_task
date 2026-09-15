"""
Requires scipy (for the per-day LP dispatch optimization in Q2b/Q2c). Run with an
interpreter that has scipy installed, e.g. a venv: `<venv>/bin/python3 analysis/q2_revenue.py`.
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

SOLAR_MW = 300
INV_MW = 250
STOR_MW = 50
STOR_MWH = 200

# ---------- Q2a: Standalone Solar ----------
solar_revenue = 0.0
solar_energy = 0.0
clipped_energy = 0.0
for row in rows:
    dc = row['shape'] * SOLAR_MW
    delivered = min(dc, INV_MW)
    solar_energy += delivered
    clipped_energy += max(0, dc - INV_MW)
    solar_revenue += delivered * row['price']

print('=== Q2a: Standalone Solar ===')
print(f'Delivered energy: {solar_energy:,.0f} MWh')
print(f'Clipped/curtailed energy: {clipped_energy:,.0f} MWh ({100*clipped_energy/(solar_energy+clipped_energy):.2f}% of gross)')
print(f'2023 backcast revenue: ${solar_revenue:,.0f}')
print(f'Revenue per delivered MWh (avg capture price): ${solar_revenue/solar_energy:.2f}/MWh')
print(f'Revenue per kW-DC: ${solar_revenue/(SOLAR_MW*1000):,.2f}/kW-DC')
print()

by_day = defaultdict(list)
for row in rows:
    by_day[row['ts'].date()].append(row)


def optimize_standalone_day(prices):
    """Per-day LP: maximize sum(price_h * (discharge_h - charge_h)) subject to a 50 MW
    power limit, a 200 MWh state-of-charge limit at every hour, 100% round-trip
    efficiency, and SOC starting the day at 0. Allows the optimizer to find multiple
    cycles within a day when price swings make it profitable, rather than assuming
    exactly one fixed 4-hour cycle."""
    n = len(prices)
    prices = np.array(prices)
    c_obj = np.concatenate([prices, -prices])  # [charge cost coefs, -discharge revenue coefs]
    A_ub, b_ub = [], []
    for t in range(1, n + 1):
        upper = np.zeros(2 * n)
        upper[:t] = 1.0        # +charge_1..t
        upper[n:n + t] = -1.0  # -discharge_1..t   => SOC_t <= 200 MWh
        A_ub.append(upper); b_ub.append(STOR_MWH)
        A_ub.append(-upper); b_ub.append(0.0)      # SOC_t >= 0
    bounds = [(0, STOR_MW)] * (2 * n)
    res = linprog(c_obj, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method='highs')
    charge, discharge = res.x[:n], res.x[n:]
    return charge, discharge, float(np.sum(prices * (discharge - charge)))


def optimize_combined_day(prices, clip_mw):
    """Same per-day LP as standalone, except each hour's charging can first draw up to
    min(clip_mw_that_hour, 50 MW) for $0 (otherwise-clipped solar) before any additional
    charging that hour is priced at the grid price."""
    n = len(prices)
    prices = np.array(prices)
    free_cap = np.minimum(np.array(clip_mw), STOR_MW)
    c_obj = np.concatenate([np.zeros(n), prices, -prices])  # [free charge (0 cost), grid charge, -discharge]
    A_ub, b_ub = [], []
    for t in range(1, n + 1):
        upper = np.zeros(3 * n)
        upper[:t] = 1.0             # +c_free_1..t
        upper[n:n + t] = 1.0        # +c_grid_1..t
        upper[2 * n:2 * n + t] = -1.0  # -discharge_1..t
        A_ub.append(upper); b_ub.append(STOR_MWH)
        A_ub.append(-upper); b_ub.append(0.0)
    for t in range(n):  # per-hour charger power cap: c_free_t + c_grid_t <= 50 MW
        row = np.zeros(3 * n)
        row[t] = 1.0
        row[n + t] = 1.0
        A_ub.append(row); b_ub.append(STOR_MW)
    bounds = [(0, free_cap[i]) for i in range(n)] + [(0, STOR_MW)] * n + [(0, STOR_MW)] * n
    res = linprog(c_obj, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method='highs')
    c_free, c_grid, discharge = res.x[:n], res.x[n:2 * n], res.x[2 * n:]
    rev = float(np.sum(prices * discharge) - np.sum(prices * c_grid))
    return c_free, c_grid, discharge, rev


# ---------- Q2b: Standalone Storage (multi-cycle LP-optimized dispatch) ----------
storage_revenue = 0.0
n_days = 0
for day, day_rows in by_day.items():
    day_rows_sorted = sorted(day_rows, key=lambda x: x['ts'])
    prices = [h['price'] for h in day_rows_sorted]
    _, _, day_rev = optimize_standalone_day(prices)
    storage_revenue += day_rev
    n_days += 1

print('=== Q2b: Standalone Storage ===')
print('Assumption: per-day linear-program dispatch (50 MW power limit, 200 MWh energy limit,')
print('SOC starts each day at 0), perfect day-ahead price foresight, round-trip efficiency = 100%')
print('(per given assumption), no degradation/cycling cost. The optimizer is free to find multiple')
print('charge/discharge cycles within a day when price swings justify it, rather than assuming')
print('exactly one fixed 4-hour cycle.')
print(f'Days modeled: {n_days}')
print(f'2023 backcast revenue: ${storage_revenue:,.0f}')
print(f'Revenue per kW (of power capacity): ${storage_revenue/(STOR_MW*1000):,.2f}/kW')
print(f'Revenue per kWh (of energy capacity): ${storage_revenue/(STOR_MWH*1000):,.2f}/kWh')
print()

# ---------- Q2c: Combined Solar + Storage ----------
# Storage charges preferentially from otherwise-clipped/curtailed solar (zero cost, since that
# energy would be wasted in the standalone case) up to STOR_MW per hour; any remaining energy
# needed is bought from the grid. Same per-day LP as Q2b otherwise (multi-cycle allowed).
combined_solar_revenue = 0.0
combined_storage_revenue = 0.0
clipped_used_total = 0.0
grid_charged_total = 0.0

for day, day_rows in by_day.items():
    for h in day_rows:
        dc = h['shape'] * SOLAR_MW
        delivered = min(dc, INV_MW)
        combined_solar_revenue += delivered * h['price']

    day_rows_sorted = sorted(day_rows, key=lambda x: x['ts'])
    prices = [h['price'] for h in day_rows_sorted]
    clip_mw = [max(0.0, h['shape'] * SOLAR_MW - INV_MW) for h in day_rows_sorted]
    c_free, c_grid, discharge, day_rev = optimize_combined_day(prices, clip_mw)
    combined_storage_revenue += day_rev
    clipped_used_total += float(np.sum(c_free))
    grid_charged_total += float(np.sum(c_grid))

combined_total = combined_solar_revenue + combined_storage_revenue
standalone_sum = solar_revenue + storage_revenue

print('=== Q2c: Combined Solar + Storage ===')
print(f'Clipped solar energy used for "free" storage charging: {clipped_used_total:,.0f} MWh')
print(f'Grid-charged energy (storage): {grid_charged_total:,.0f} MWh')
print(f'Combined solar revenue: ${combined_solar_revenue:,.0f}')
print(f'Combined storage revenue: ${combined_storage_revenue:,.0f}')
print(f'Combined system total revenue: ${combined_total:,.0f}')
print()
print(f'Sum of standalone solar + standalone storage: ${standalone_sum:,.0f}')
print(f'Interaction benefit (combined - sum of standalone): ${combined_total - standalone_sum:,.0f}')
print(f'Interaction benefit as % of standalone sum: {100*(combined_total-standalone_sum)/standalone_sum:.4f}%')
