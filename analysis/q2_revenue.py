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

SOLAR_MW = 300
INV_MW = 250
STOR_MW = 50
STOR_MWH = 200
DURATION_HR = STOR_MWH / STOR_MW  # 4 hours

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

# group rows by day for daily dispatch
by_day = defaultdict(list)
for row in rows:
    by_day[row['ts'].date()].append(row)

# ---------- Q2b: Standalone Storage (perfect real-time foresight, 1 cycle/day, RTE=1) ----------
storage_revenue = 0.0
n_full_cycle_days = 0
for day, day_rows in by_day.items():
    day_rows_sorted = sorted(day_rows, key=lambda x: x['price'])
    n_charge_hrs = min(int(DURATION_HR), len(day_rows_sorted))
    charge_hrs = day_rows_sorted[:n_charge_hrs]
    discharge_hrs = day_rows_sorted[-n_charge_hrs:]
    charge_cost = sum(h['price'] for h in charge_hrs) * STOR_MW
    discharge_rev = sum(h['price'] for h in discharge_hrs) * STOR_MW
    storage_revenue += (discharge_rev - charge_cost)
    n_full_cycle_days += 1

print('=== Q2b: Standalone Storage ===')
print(f'Assumption: 1 full charge/discharge cycle per day, {DURATION_HR:.0f}-hr duration (200 MWh / 50 MW),')
print('perfect real-time price foresight, round-trip efficiency = 100% (per given assumption), no degradation/cycling cost.')
print(f'Days modeled: {n_full_cycle_days}')
print(f'2023 backcast revenue: ${storage_revenue:,.0f}')
print(f'Revenue per kW (of power capacity): ${storage_revenue/(STOR_MW*1000):,.2f}/kW')
print(f'Revenue per kWh (of energy capacity): ${storage_revenue/(STOR_MWH*1000):,.2f}/kWh')
print()

# ---------- Q2c: Combined Solar + Storage ----------
# Storage charges preferentially from otherwise-clipped/curtailed solar (zero cost, since that
# energy would be wasted in the standalone case) up to STOR_MW per hour; any remaining energy
# needed to fill the daily 200 MWh charge target is bought from the grid at that day's next-lowest
# price hours (mirroring Q2b). Discharge strategy unchanged (day's top-4 price hours, sold to grid).
combined_solar_revenue = 0.0
combined_storage_revenue = 0.0
clipped_used_total = 0.0
grid_charged_total = 0.0

for day, day_rows in by_day.items():
    # Solar delivered revenue - identical to standalone solar
    for h in day_rows:
        dc = h['shape'] * SOLAR_MW
        delivered = min(dc, INV_MW)
        combined_solar_revenue += delivered * h['price']

    # Available clipped solar per hour this day
    clip_by_hour = {h['ts'].hour: max(0, h['shape']*SOLAR_MW - INV_MW) for h in day_rows}
    price_by_hour = {h['ts'].hour: h['price'] for h in day_rows}

    energy_needed = STOR_MWH
    charge_cost = 0.0
    # Step 1: use free clipped solar first (capped at STOR_MW/hr and by energy_needed)
    for hr, clip_mw in clip_by_hour.items():
        take = min(clip_mw, STOR_MW, energy_needed)
        if take > 0:
            energy_needed -= take
            clipped_used_total += take
            # cost = $0 (would otherwise be curtailed)

    # Step 2: fill remainder from grid at lowest-price hours not already used for clipped charging
    # (exclude hours that had clipped solar charging from being reused, though grid MW is separate
    # capacity headroom in the same hour is ignored for simplicity given negligible magnitude)
    remaining_hours_sorted = sorted(
        [h for h in day_rows if clip_by_hour[h['ts'].hour] == 0],
        key=lambda x: x['price']
    )
    n_grid_hrs = min(int(DURATION_HR), len(remaining_hours_sorted))
    grid_hrs = remaining_hours_sorted[:n_grid_hrs]
    grid_mwh_this_hr = min(STOR_MW, energy_needed / n_grid_hrs) if n_grid_hrs else 0
    for h in grid_hrs:
        take = min(STOR_MW, energy_needed)
        charge_cost += take * h['price']
        grid_charged_total += take
        energy_needed -= take
        if energy_needed <= 0:
            break

    # Discharge: day's top-4 price hours (same as standalone)
    discharge_hrs = sorted(day_rows, key=lambda x: x['price'])[-int(DURATION_HR):]
    discharge_rev = sum(h['price'] for h in discharge_hrs) * STOR_MW

    combined_storage_revenue += (discharge_rev - charge_cost)

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
print(f'Interaction benefit as % of standalone sum: {100*(combined_total-standalone_sum)/standalone_sum:.3f}%')
