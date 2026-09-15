import csv
from collections import defaultdict
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

da_sums = defaultdict(float)
rt_sums = defaultdict(float)
counts = defaultdict(int)

with open('hourly_data.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.strptime(row['weather year EST hour beginning'], '%Y-%m-%d %H:%M:%S')
        da_sums[ts.month] += float(row['NYISO (NYC Zone) Historical Day Ahead Energy Price ($/MWh)'])
        rt_sums[ts.month] += float(row['NYISO (NYC Zone) Real Time Energy Price ($/MWh)'])
        counts[ts.month] += 1

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
da_avgs = [da_sums[m]/counts[m] for m in range(1, 13)]
rt_avgs = [rt_sums[m]/counts[m] for m in range(1, 13)]
da_annual = sum(da_sums.values()) / sum(counts.values())
rt_annual = sum(rt_sums.values()) / sum(counts.values())

# Write CSV
with open('no_interconnection_limit/monthly_da_rt_price_2023.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Month', 'Avg NYISO NYC Day-Ahead Price ($/MWh)', 'Avg NYISO NYC Real-Time Price ($/MWh)'])
    for m, da, rt in zip(months, da_avgs, rt_avgs):
        w.writerow([m, round(da, 2), round(rt, 2)])
    w.writerow(['Annual Average', round(da_annual, 2), round(rt_annual, 2)])

# Chart — grouped bar, dataviz skill mark spec (light mode)
BLUE = '#2a78d6'     # series 1: day-ahead
ORANGE = '#eb6834'   # series 2: real-time
INK_PRIMARY = '#0b0b0b'
INK_SECONDARY = '#52514e'
INK_MUTED = '#898781'
GRIDLINE = '#e1e0d9'
BASELINE = '#c3c2b7'
SURFACE = '#fcfcfb'

x = np.arange(12)
width = 0.36

fig, ax = plt.subplots(figsize=(10, 5.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

bars_da = ax.bar(x - width/2, da_avgs, width, color=BLUE, zorder=3, label='Day-Ahead')
bars_rt = ax.bar(x + width/2, rt_avgs, width, color=ORANGE, zorder=3, label='Real-Time')

for rect, val in zip(bars_da, da_avgs):
    ax.text(rect.get_x() + rect.get_width()/2, val + 0.9, f'${val:.0f}',
            ha='center', va='bottom', fontsize=8, color=INK_PRIMARY)
for rect, val in zip(bars_rt, rt_avgs):
    ax.text(rect.get_x() + rect.get_width()/2, val + 0.9, f'${val:.0f}',
            ha='center', va='bottom', fontsize=8, color=INK_PRIMARY)

ax.set_ylabel('Avg. Energy Price ($/MWh)', color=INK_PRIMARY, fontsize=13)
ax.set_title('NYISO N.Y.C. Zone — Monthly Average Day-Ahead vs. Real-Time Price, 2023',
             color=INK_PRIMARY, fontsize=13, fontweight='bold', pad=14, loc='left')

ax.set_xticks(x)
ax.set_xticklabels(months)
ax.set_ylim(0, max(da_avgs + rt_avgs) * 1.22)
ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='x', colors=INK_SECONDARY, length=0, labelsize=10)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)

legend = ax.legend(loc='upper right', frameon=False, fontsize=10, labelcolor=INK_SECONDARY)

plt.tight_layout()
plt.savefig('no_interconnection_limit/monthly_da_rt_price_2023.png', facecolor=SURFACE)
print('Wrote no_interconnection_limit/monthly_da_rt_price_2023.csv and no_interconnection_limit/monthly_da_rt_price_2023.png')
for m, da, rt in zip(months, da_avgs, rt_avgs):
    print(f'{m}: DA ${da:.2f}/MWh | RT ${rt:.2f}/MWh')
print(f'Annual: DA ${da_annual:.2f}/MWh | RT ${rt_annual:.2f}/MWh')
