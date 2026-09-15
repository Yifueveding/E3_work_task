import csv
from collections import defaultdict
from datetime import datetime
import statistics
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

rows = []
with open('hourly_data.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.strptime(row['weather year EST hour beginning'], '%Y-%m-%d %H:%M:%S')
        rows.append({
            'ts': ts,
            'da': float(row['NYISO (NYC Zone) Historical Day Ahead Energy Price ($/MWh)']),
            'rt': float(row['NYISO (NYC Zone) Real Time Energy Price ($/MWh)']),
        })

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
daily = defaultdict(list)
monthly_da_rt_gap = defaultdict(list)
for row in rows:
    daily[row['ts'].date()].append(row['da'])
    monthly_da_rt_gap[row['ts'].month].append(abs(row['da'] - row['rt']))

monthly_spreads = defaultdict(list)
for day, prices in daily.items():
    monthly_spreads[day.month].append(max(prices) - min(prices))

spreads = [statistics.mean(monthly_spreads[m]) for m in range(1,13)]
da_rt_gap = [statistics.mean(monthly_da_rt_gap[m]) for m in range(1,13)]
annual_avg = statistics.mean([s for v in monthly_spreads.values() for s in v])
annual_gap_avg = statistics.mean([g for v in monthly_da_rt_gap.values() for g in v])

BLUE, ORANGE = '#2a78d6', '#eb6834'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'
HIGHLIGHT = '#fab21933'  # translucent highlight band (warning-yellow @ 20% alpha)

# Best month: above-average daily spread (big arbitrage opportunity) paired
# with the smallest DA-RT gap among those months (little real-time basis risk).
above_avg_months = [i for i in range(12) if spreads[i] >= annual_avg]
best_idx = min(above_avg_months, key=lambda i: da_rt_gap[i])

fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

ax.axvspan(best_idx - 0.5, best_idx + 0.5, color=HIGHLIGHT, zorder=1)

x = np.arange(12)
w = 0.36
bars1 = ax.bar(x - w/2, spreads, width=w, color=BLUE, zorder=3)
bars2 = ax.bar(x + w/2, da_rt_gap, width=w, color=ORANGE, zorder=3)

for rect, val in zip(bars1, spreads):
    ax.text(rect.get_x()+rect.get_width()/2, val+1.0, f'${val:.0f}', ha='center', va='bottom', fontsize=8, color=INK_PRIMARY)
for rect, val in zip(bars2, da_rt_gap):
    ax.text(rect.get_x()+rect.get_width()/2, val+1.0, f'${val:.0f}', ha='center', va='bottom', fontsize=8, color=INK_PRIMARY)

ax.set_xticks(x); ax.set_xticklabels(months, color=INK_SECONDARY, fontsize=10)
ax.set_ylabel('Avg. Price Gap ($/MWh)', color=INK_PRIMARY, fontsize=13)
ax.set_title('Storage Arbitrage Opportunity by Month, 2023 (NYISO N.Y.C.)',
             color=INK_PRIMARY, fontsize=12.5, fontweight='bold', pad=14, loc='left')
ax.annotate('Large spread,\nlow DA-RT gap', xy=(best_idx, spreads[best_idx] + 2),
            xytext=(best_idx, spreads[best_idx] + 12),
            ha='center', va='bottom', fontsize=9.5, color=INK_PRIMARY, fontweight='bold',
            arrowprops=dict(arrowstyle='-', color=INK_MUTED, lw=1.1))

ax.set_ylim(0, max(spreads + da_rt_gap)*1.35)
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top','right','left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='x', length=0)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)

legend_handles = [
    Patch(facecolor=BLUE, label='Avg. Daily Day-Ahead Price Spread (max−min)'),
    Patch(facecolor=ORANGE, label='Avg. Hourly |Day-Ahead − Real-Time| Gap'),
]
ax.legend(handles=legend_handles, loc='upper left', frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY)

plt.tight_layout()
plt.savefig('no_interconnection_limit/storage_value_by_month.png', facecolor=SURFACE)
print('saved storage_value_by_month.png')
for i, m in enumerate(months):
    print(f'{m}: daily_spread=${spreads[i]:.2f}/MWh  da_rt_gap=${da_rt_gap[i]:.2f}/MWh')
print(f'Annual avg: daily_spread=${annual_avg:.2f}/MWh  da_rt_gap=${annual_gap_avg:.2f}/MWh')
