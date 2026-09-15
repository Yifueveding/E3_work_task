"""
Combines no_interconnection_limit/q2_energy_only_by_config.png and
interconnection_scenario/q2_energy_only_by_config_interconnection.png into a single
grouped bar chart: for each configuration (Standalone Solar, Standalone Storage,
Combined Solar + Storage), the no-POI-limit bar and the 150 MW interconnection-limit
bar sit side by side, each stacked into its solar/storage revenue components.

Data sources:
- No limit: no_interconnection_limit/q2_reserve_chart.py (energy_rev / combined_solar_component / combined_storage_component)
- 150 MW limit: interconnection_scenario/q2_energy_only_chart_interconnection.py
"""
import matplotlib.pyplot as plt
import numpy as np

# No interconnection limit (base case)
no_limit_solar = 18_803_819
no_limit_storage = 1_977_954
no_limit_combined_solar = 18_803_819
no_limit_combined_storage = 1_987_978

# 150 MW interconnection limit
lim150_solar = 15_701_216
lim150_storage = 1_977_954
lim150_combined_solar = 14_701_366
lim150_combined_storage = 4_341_051

BLUE, ORANGE = '#2a78d6', '#eb6834'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

labels = ['Standalone\nSolar', 'Standalone\nStorage', 'Combined\nSolar + Storage']
group_x = np.array([0, 1, 2])
width = 0.32
offset = width / 2 + 0.02

no_limit_solar_m = np.array([no_limit_solar, 0, no_limit_combined_solar]) / 1e6
no_limit_storage_m = np.array([0, no_limit_storage, no_limit_combined_storage]) / 1e6
lim150_solar_m = np.array([lim150_solar, 0, lim150_combined_solar]) / 1e6
lim150_storage_m = np.array([0, lim150_storage, lim150_combined_storage]) / 1e6

no_limit_total_m = no_limit_solar_m + no_limit_storage_m
lim150_total_m = lim150_solar_m + lim150_storage_m

fig, ax = plt.subplots(figsize=(11, 5.8), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

x_no_limit = group_x - offset
x_lim150 = group_x + offset

ax.bar(x_no_limit, no_limit_solar_m, width=width, color=BLUE, zorder=3, label='Solar revenue component')
ax.bar(x_no_limit, no_limit_storage_m, width=width, bottom=no_limit_solar_m, color=ORANGE, zorder=3,
       label='Storage revenue component')
ax.bar(x_lim150, lim150_solar_m, width=width, color=BLUE, zorder=3, hatch='///', edgecolor=SURFACE, linewidth=0.6)
ax.bar(x_lim150, lim150_storage_m, width=width, bottom=lim150_solar_m, color=ORANGE, zorder=3,
       hatch='///', edgecolor=SURFACE, linewidth=0.6)

# Totals above each bar
for xi, t in zip(x_no_limit, no_limit_total_m):
    if t > 0:
        ax.text(xi, t + 0.4, f'${t:.1f}M', ha='center', va='bottom', fontsize=10, color=INK_PRIMARY, fontweight='bold')
for xi, t in zip(x_lim150, lim150_total_m):
    if t > 0:
        ax.text(xi, t + 0.4, f'${t:.1f}M', ha='center', va='bottom', fontsize=10, color=INK_PRIMARY, fontweight='bold')

# Segment labels on the combined bars only (index 2)
def label_segment(xi, base, seg, text_color='white'):
    if seg > 0.5:
        ax.text(xi, base + seg / 2, f'${seg:.1f}M', ha='center', va='center', fontsize=8.5, color=text_color, fontweight='bold')

label_segment(x_no_limit[2], 0, no_limit_solar_m[2])
label_segment(x_no_limit[2], no_limit_solar_m[2], no_limit_storage_m[2])
label_segment(x_lim150[2], 0, lim150_solar_m[2])
label_segment(x_lim150[2], lim150_solar_m[2], lim150_storage_m[2])

YMAX = max(no_limit_total_m.max(), lim150_total_m.max()) * 1.38
ax.set_xticks(group_x); ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=11)
ax.set_ylabel('2023 Backcast Revenue ($M)', color=INK_PRIMARY, fontsize=13)
ax.set_title('Energy-Only Revenue by Configuration: No Interconnection Limit vs. 150 MW Limit',
              color=INK_PRIMARY, fontsize=14, fontweight='bold', pad=48, loc='left')
ax.set_ylim(0, YMAX)
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=12)
ax.tick_params(axis='x', length=0)

# Component legend (color) + scenario legend (hatch) side by side
component_handles = [
    plt.Rectangle((0, 0), 1, 1, facecolor=BLUE, label='Solar revenue component'),
    plt.Rectangle((0, 0), 1, 1, facecolor=ORANGE, label='Storage revenue component'),
]
scenario_handles = [
    plt.Rectangle((0, 0), 1, 1, facecolor=INK_MUTED, edgecolor=SURFACE, label='No interconnection limit'),
    plt.Rectangle((0, 0), 1, 1, facecolor=INK_MUTED, edgecolor=SURFACE, hatch='///', label='150 MW interconnection limit'),
]
all_handles = component_handles + scenario_handles
ax.legend(handles=all_handles, loc='upper center', frameon=False, fontsize=9.5, ncol=4,
          labelcolor=INK_SECONDARY, bbox_to_anchor=(0.5, 1.13), columnspacing=1.4, handletextpad=0.6)

plt.tight_layout()
plt.savefig('q2_energy_only_combined.png', facecolor=SURFACE)
print('saved q2_energy_only_combined.png')
