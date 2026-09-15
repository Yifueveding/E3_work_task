import csv
from collections import defaultdict
from datetime import datetime
import statistics

rows = []
with open('hourly_data.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.strptime(row['weather year EST hour beginning'], '%Y-%m-%d %H:%M:%S')
        rows.append({
            'ts': ts,
            'solar': float(row['Solar Shape (Normalized)']),
            'da': float(row['NYISO (NYC Zone) Historical Day Ahead Energy Price ($/MWh)']),
        })

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# ---- Solar: generation-weighted (capture) price by month, and share of annual generation ----
gen_weighted_num = defaultdict(float)
gen_weighted_den = defaultdict(float)
flat_sum = defaultdict(float)
flat_cnt = defaultdict(int)
for row in rows:
    m = row['ts'].month
    gen_weighted_num[m] += row['solar'] * row['da']
    gen_weighted_den[m] += row['solar']
    flat_sum[m] += row['da']
    flat_cnt[m] += 1

total_gen = sum(gen_weighted_den.values())
print('=== SOLAR ===')
print(f'{"Month":5} {"CapturePx":>10} {"FlatAvgPx":>10} {"Capture%ofFlat":>15} {"%ofAnnualGen":>13}')
for i, m in enumerate(range(1,13)):
    cap = gen_weighted_num[m] / gen_weighted_den[m]
    flat = flat_sum[m] / flat_cnt[m]
    pct_gen = 100 * gen_weighted_den[m] / total_gen
    print(f'{months[i]:5} {cap:10.2f} {flat:10.2f} {100*cap/flat:14.1f}% {pct_gen:12.1f}%')

annual_cap = sum(gen_weighted_num.values()) / sum(gen_weighted_den.values())
annual_flat = sum(flat_sum.values()) / sum(flat_cnt.values())
print(f'Annual capture price: {annual_cap:.2f} vs flat avg: {annual_flat:.2f} (capture rate {100*annual_cap/annual_flat:.1f}%)')

# ---- Solar: average normalized shape by hour of day (summer vs winter) to show daily timing ----
print()
print('=== SOLAR SHAPE: avg output by hour-of-day, Jun-Aug vs Dec-Feb ===')
summer_hr = defaultdict(list)
winter_hr = defaultdict(list)
for row in rows:
    if row['ts'].month in (6,7,8):
        summer_hr[row['ts'].hour].append(row['solar'])
    if row['ts'].month in (12,1,2):
        winter_hr[row['ts'].hour].append(row['solar'])
for h in range(24):
    s = statistics.mean(summer_hr[h]) if summer_hr[h] else 0
    w = statistics.mean(winter_hr[h]) if winter_hr[h] else 0
    print(f'{h:02d}:00  summer={s:.2f}  winter={w:.2f}')

# ---- Storage: price volatility by month (daily max-min spread, avg) ----
print()
print('=== STORAGE: avg daily DA price spread (max-min) by month ===')
daily = defaultdict(list)
for row in rows:
    key = row['ts'].date()
    daily[key].append(row['da'])

monthly_spreads = defaultdict(list)
monthly_std = defaultdict(list)
for day, prices in daily.items():
    m = day.month
    monthly_spreads[m].append(max(prices) - min(prices))
    monthly_std[m].append(statistics.pstdev(prices))

print(f'{"Month":5} {"AvgDailySpread":>15} {"AvgHourlyStdev":>15}')
for i, m in enumerate(range(1,13)):
    avg_spread = statistics.mean(monthly_spreads[m])
    avg_std = statistics.mean(monthly_std[m])
    print(f'{months[i]:5} {avg_spread:15.2f} {avg_std:15.2f}')

overall_avg_spread = statistics.mean([s for v in monthly_spreads.values() for s in v])
print(f'Annual avg daily spread: {overall_avg_spread:.2f}')
