import csv
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

rows = []
with open('hourly_data.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.strptime(row['weather year EST hour beginning'], '%Y-%m-%d %H:%M:%S')
        rows.append({'ts': ts, 'solar': float(row['Solar Shape (Normalized)']),
                     'da': float(row['NYISO (NYC Zone) Historical Day Ahead Energy Price ($/MWh)'])})

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
gen_num = defaultdict(float); gen_den = defaultdict(float)
flat_sum = defaultdict(float); flat_cnt = defaultdict(int)
for row in rows:
    m = row['ts'].month
    gen_num[m] += row['solar']*row['da']; gen_den[m] += row['solar']
    flat_sum[m] += row['da']; flat_cnt[m] += 1

capture = [gen_num[m]/gen_den[m] for m in range(1,13)]
flat = [flat_sum[m]/flat_cnt[m] for m in range(1,13)]
gen_share = [100*gen_den[m]/sum(gen_den.values()) for m in range(1,13)]

BLUE, DARK_BLUE, ORANGE = '#2a78d6', '#184f95', '#eb6834'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

fig, ax1 = plt.subplots(figsize=(9.5, 5.2), dpi=200)
fig.patch.set_facecolor(SURFACE); ax1.set_facecolor(SURFACE)

x = np.arange(12)
w = 0.36
capture_colors = [DARK_BLUE if capture[i] > flat[i] else BLUE for i in range(12)]

ax1.bar(x - w/2, flat, width=w, color='#c3c2b7', label='Monthly Average Price', zorder=3)
ax1.bar(x + w/2, capture, width=w, color=capture_colors, zorder=3)

from matplotlib.patches import Patch
legend_handles = [
    Patch(facecolor='#c3c2b7', label='Monthly Average Price'),
    Patch(facecolor=DARK_BLUE, label='Solar Energy Price — above monthly average'),
    Patch(facecolor=BLUE, label='Solar Energy Price — at/below monthly average'),
]

ax1.set_xticks(x); ax1.set_xticklabels(months, color=INK_SECONDARY, fontsize=10)
ax1.set_ylabel('$/MWh', color=INK_PRIMARY, fontsize=13)
ax1.set_ylim(0, max(flat+capture)*1.25)
ax1.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax1.set_axisbelow(True)
for s in ['top','right','left']:
    ax1.spines[s].set_visible(False)
ax1.spines['bottom'].set_color(BASELINE)
ax1.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)
ax1.tick_params(axis='x', length=0)

ax1.set_title('Solar Value by Month, 2023 (NYISO N.Y.C.)',
              color=INK_PRIMARY, fontsize=12.5, fontweight='bold', pad=14, loc='left')
ax1.legend(handles=legend_handles, loc='upper left', frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY)

plt.tight_layout()
plt.savefig('no_interconnection_limit/solar_value_by_month.png', facecolor=SURFACE)
print('saved solar_value_by_month.png')
for i,m in enumerate(months):
    print(f'{m}: capture={capture[i]:.2f} flat={flat[i]:.2f} genshare={gen_share[i]:.1f}%')
