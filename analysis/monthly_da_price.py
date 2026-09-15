import csv
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

sums = defaultdict(float)
counts = defaultdict(int)

with open('hourly_data.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.strptime(row['weather year EST hour beginning'], '%Y-%m-%d %H:%M:%S')
        price = float(row['NYISO (NYC Zone) Historical Day Ahead Energy Price ($/MWh)'])
        sums[ts.month] += price
        counts[ts.month] += 1

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
avgs = [sums[m]/counts[m] for m in range(1, 13)]
annual_avg = sum(sums.values()) / sum(counts.values())

# Write CSV
with open('analysis/monthly_da_price_2023.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Month', 'Avg NYISO NYC Day-Ahead Price ($/MWh)'])
    for m, a in zip(months, avgs):
        w.writerow([m, round(a, 2)])
    w.writerow(['Annual Average', round(annual_avg, 2)])

# Chart — single-series bar, dataviz skill mark spec (light mode)
BLUE = '#2a78d6'
INK_PRIMARY = '#0b0b0b'
INK_SECONDARY = '#52514e'
INK_MUTED = '#898781'
GRIDLINE = '#e1e0d9'
BASELINE = '#c3c2b7'
SURFACE = '#fcfcfb'

fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

bars = ax.bar(months, avgs, color=BLUE, width=0.62, zorder=3)

ax.axhline(annual_avg, color=INK_MUTED, linestyle=(0, (3, 3)), linewidth=1.2, zorder=2)
ax.text(11.55, annual_avg, f'2023 avg: ${annual_avg:.0f}/MWh',
        color=INK_SECONDARY, fontsize=9.5, va='center', ha='left')

for rect, val in zip(bars, avgs):
    ax.text(rect.get_x() + rect.get_width()/2, val + 0.9, f'${val:.0f}',
            ha='center', va='bottom', fontsize=9, color=INK_PRIMARY)

ax.set_ylabel('Avg. Day-Ahead Price ($/MWh)', color=INK_PRIMARY, fontsize=13)
ax.set_title('NYISO N.Y.C. Zone — Monthly Average Day-Ahead Energy Price, 2023',
             color=INK_PRIMARY, fontsize=13, fontweight='bold', pad=14, loc='left')

ax.set_ylim(0, max(avgs) * 1.22)
ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='x', colors=INK_SECONDARY, length=0, labelsize=10)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)

plt.tight_layout()
plt.savefig('analysis/monthly_da_price_2023.png', facecolor=SURFACE)
print('Wrote analysis/monthly_da_price_2023.csv and analysis/monthly_da_price_2023.png')
for m, a in zip(months, avgs):
    print(f'{m}: ${a:.2f}/MWh')
print(f'Annual: ${annual_avg:.2f}/MWh')
