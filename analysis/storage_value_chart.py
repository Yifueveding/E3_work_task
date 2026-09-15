import csv
from collections import defaultdict
from datetime import datetime
import statistics
import matplotlib.pyplot as plt

rows = []
with open('hourly_data.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.strptime(row['weather year EST hour beginning'], '%Y-%m-%d %H:%M:%S')
        rows.append({'ts': ts, 'da': float(row['NYISO (NYC Zone) Historical Day Ahead Energy Price ($/MWh)'])})

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
daily = defaultdict(list)
for row in rows:
    daily[row['ts'].date()].append(row['da'])

monthly_spreads = defaultdict(list)
for day, prices in daily.items():
    monthly_spreads[day.month].append(max(prices) - min(prices))

spreads = [statistics.mean(monthly_spreads[m]) for m in range(1,13)]
annual_avg = statistics.mean([s for v in monthly_spreads.values() for s in v])

BLUE = '#2a78d6'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

bars = ax.bar(months, spreads, color=BLUE, width=0.62, zorder=3)
ax.axhline(annual_avg, color=INK_MUTED, linestyle=(0,(3,3)), linewidth=1.2, zorder=2)
ax.text(11.55, annual_avg, f'2023 avg: ${annual_avg:.0f}/MWh', color=INK_SECONDARY, fontsize=9.5, va='center', ha='left')

for rect, val in zip(bars, spreads):
    ax.text(rect.get_x()+rect.get_width()/2, val+1.0, f'${val:.0f}', ha='center', va='bottom', fontsize=9, color=INK_PRIMARY)

ax.set_ylabel('Avg. Daily DA Price Spread ($/MWh, max-min)', color=INK_PRIMARY, fontsize=13)
ax.set_title('Storage Arbitrage Opportunity by Month: Avg. Daily Day-Ahead Price Spread, 2023',
             color=INK_PRIMARY, fontsize=12.5, fontweight='bold', pad=14, loc='left')
ax.set_ylim(0, max(spreads)*1.25)
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top','right','left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='x', colors=INK_SECONDARY, length=0, labelsize=10)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)

plt.tight_layout()
plt.savefig('analysis/storage_value_by_month.png', facecolor=SURFACE)
print('saved storage_value_by_month.png')
