"""
Q2d (extension, beyond the base exercise): NYISO operating reserve (headroom/footroom)
scenario. Estimates additional revenue from offering reserve capacity on top of the
energy-only backcast in q2_revenue.py, at an assumed reserve price of $1.25/MW-hr
(midpoint of the $1-1.5/MW range).

Headroom = capacity available to INCREASE output on call (up-reserve).
Footroom = capacity available to DECREASE output on call (down-reserve).

Assumptions (nameplate-based, state-dependent — see chat for alternatives considered):
  Solar   - cannot provide reserve. It is a variable, weather-dependent resource with no
            firm/dispatchable capacity commitment, so it does not qualify to offer NYISO
            reserve products; standalone solar earns $0 reserve revenue.
  Storage - reuses the same daily charge/discharge schedule as q2_revenue.py (4 lowest-
            price hours charge, 4 highest-price hours discharge, 16 hours idle), determined
            from real-time prices. While charging, it is already using its full 50 MW to
            charge, so it can offer 50 MW of footroom (charge even more/stop faster) but no
            headroom. While discharging, the reverse: 50 MW headroom, no footroom. While
            idle, it can offer the full 50 MW of headroom AND the full 50 MW of footroom
            simultaneously (it could ramp to +50 MW discharge or -50 MW charge from a
            standing start).
  Combined - all reserve capacity comes from the storage component only (identical
            schedule to standalone storage); the solar component still cannot offer
            reserve.

Energy-only revenue figures below are taken directly from q2_revenue.py's real-time-price
output (not recomputed here) so this script only needs to add the incremental reserve
revenue on top.
"""
import csv
from datetime import datetime
from collections import defaultdict

rows = []
with open('hourly_data.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.strptime(row['weather year EST hour beginning'], '%Y-%m-%d %H:%M:%S')
        rows.append({
            'ts': ts,
            'shape': float(row['Solar Shape (Normalized)']),
            'price': float(row['NYISO (NYC Zone) Real Time Energy Price ($/MWh)']),
        })

STOR_MW = 50
STOR_MWH = 200
DURATION_HR = STOR_MWH / STOR_MW  # 4 hours
RESERVE_PRICE = 1.25  # $/MW-hr, midpoint of the $1-1.5/MW NYISO reserve range

# Energy-only 2023 backcast revenue, real-time price basis (from q2_revenue.py)
ENERGY_REVENUE = {
    'solar': 18_910_425,
    'storage': 2_473_753,
    'combined': 21_391_036,
}

by_day = defaultdict(list)
for row in rows:
    by_day[row['ts'].date()].append(row)

# ---------- Storage headroom / footroom (schedule from real-time-price dispatch) ----------
storage_headroom_mwh = 0.0
storage_footroom_mwh = 0.0
n_charge_hrs_total = n_discharge_hrs_total = n_idle_hrs_total = 0

for day, day_rows in by_day.items():
    day_rows_sorted = sorted(day_rows, key=lambda x: x['price'])
    n = min(int(DURATION_HR), len(day_rows_sorted))
    # Classify directly off the sorted list (not by timestamp) since Nov 5's fall-back
    # DST day repeats an "01:00:00" label, which would collide if matched back by ts.
    charge_rows = day_rows_sorted[:n]
    discharge_rows = day_rows_sorted[-n:]
    idle_rows = day_rows_sorted[n:len(day_rows_sorted) - n]

    storage_footroom_mwh += STOR_MW * len(charge_rows)
    n_charge_hrs_total += len(charge_rows)

    storage_headroom_mwh += STOR_MW * len(discharge_rows)
    n_discharge_hrs_total += len(discharge_rows)

    storage_headroom_mwh += STOR_MW * len(idle_rows)
    storage_footroom_mwh += STOR_MW * len(idle_rows)
    n_idle_hrs_total += len(idle_rows)

storage_reserve_mwh = storage_headroom_mwh + storage_footroom_mwh
storage_reserve_revenue = storage_reserve_mwh * RESERVE_PRICE

# Solar cannot provide reserve; combined system's reserve comes from storage only.
solar_reserve_revenue = 0.0
combined_reserve_revenue = storage_reserve_revenue

print(f'Reserve price assumed: ${RESERVE_PRICE:.2f}/MW-hr')
print(f'Storage hours: {n_charge_hrs_total} charge, {n_discharge_hrs_total} discharge, {n_idle_hrs_total} idle')
print()

print('=== Standalone Solar ===')
print('Solar cannot provide reserve (variable, non-dispatchable resource).')
print(f'Reserve revenue: ${solar_reserve_revenue:,.0f}')
print(f'Energy-only revenue: ${ENERGY_REVENUE["solar"]:,.0f}')
print(f'Energy + reserve revenue: ${ENERGY_REVENUE["solar"] + solar_reserve_revenue:,.0f}')
print()

print('=== Standalone Storage ===')
print(f'Headroom offered: {storage_headroom_mwh:,.0f} MW-hr/yr')
print(f'Footroom offered: {storage_footroom_mwh:,.0f} MW-hr/yr')
print(f'Reserve revenue: ${storage_reserve_revenue:,.0f}')
print(f'Energy-only revenue: ${ENERGY_REVENUE["storage"]:,.0f}')
print(f'Energy + reserve revenue: ${ENERGY_REVENUE["storage"] + storage_reserve_revenue:,.0f}')
print(f'Reserve uplift: {100*storage_reserve_revenue/ENERGY_REVENUE["storage"]:.2f}%')
print()

print('=== Combined Solar + Storage ===')
print('Reserve revenue comes entirely from the storage component (solar cannot provide reserve).')
print(f'Reserve revenue: ${combined_reserve_revenue:,.0f}')
print(f'Energy-only revenue: ${ENERGY_REVENUE["combined"]:,.0f}')
print(f'Energy + reserve revenue: ${ENERGY_REVENUE["combined"] + combined_reserve_revenue:,.0f}')
print(f'Reserve uplift: {100*combined_reserve_revenue/ENERGY_REVENUE["combined"]:.2f}%')
