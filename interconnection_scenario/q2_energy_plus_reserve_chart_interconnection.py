"""
Companion to q2_energy_only_chart_interconnection.py, mirroring the style of
analysis/q2_reserve_chart.py's "Energy + Reserve" panel: stacks reserve revenue
(headroom + footroom @ $1.25/MW-hr) on top of energy revenue, by configuration, under the
150 MW interconnection-limit scenario. Shares the same y-axis scale as
q2_energy_only_by_config_interconnection.png so the two are directly comparable.

Values from interconnection_analysis.py (energy) and interconnection_reserve_scenario.py
(reserve).
"""
import matplotlib.pyplot as plt

energy_rev = {
    'solar': 15_701_216,
    'storage': 1_977_954,
    'combined': 19_042_417,
}
reserve_rev = {
    'solar': 0,
    'storage': 781_375,       # unaffected by the POI limit (50 MW << 150 MW)
    'combined': 494_824,      # reduced under the POI limit (headroom competes with solar)
}

BLUE, GREEN = '#2a78d6', '#2fa84f'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

labels = ['Standalone\nSolar', 'Standalone\nStorage', 'Combined\nSolar + Storage']
keys = ['solar', 'storage', 'combined']
x = [0, 1, 2]

energy_vals = [energy_rev[k] / 1e6 for k in keys]
reserve_vals = [reserve_rev[k] / 1e6 for k in keys]
totals = [e + r for e, r in zip(energy_vals, reserve_vals)]

# Shared y-axis scale with q2_energy_only_by_config_interconnection.png (base-case max $20.79M * 1.22)
YMAX = max(20.791797 * 1.22, max(totals) * 1.22)

fig, ax = plt.subplots(figsize=(9, 5.3), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

ax.bar(x, energy_vals, width=0.55, color=BLUE, zorder=3, label='Energy revenue (day-ahead price)')
ax.bar(x, reserve_vals, width=0.55, bottom=energy_vals, color=GREEN, zorder=3,
       label='Reserve revenue (headroom + footroom @ $1.25/MW-hr)')

for xi, e, r, t in zip(x, energy_vals, reserve_vals, totals):
    ax.text(xi, t + 0.4, f'${t:.1f}M', ha='center', va='bottom', fontsize=11, color=INK_PRIMARY, fontweight='bold')
    ax.text(xi, e / 2, f'${e:.1f}M', ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    if r > 0.5:
        ax.text(xi, e + r / 2, f'+${r:.1f}M', ha='center', va='center', fontsize=9, color='white', fontweight='bold')

ax.set_xticks(x); ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=10.5)
ax.set_ylabel('2023 Backcast Revenue ($M)', color=INK_SECONDARY, fontsize=10)
ax.set_title('Energy + Reserve Revenue by Configuration (150 MW Interconnection Limit)',
              color=INK_PRIMARY, fontsize=13, fontweight='bold', pad=14, loc='left')
ax.set_ylim(0, YMAX)
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='y', colors=INK_MUTED, length=0, labelsize=9)
ax.tick_params(axis='x', length=0)
ax.legend(loc='upper left', frameon=False, fontsize=9, labelcolor=INK_SECONDARY, bbox_to_anchor=(0.0, 1.05))

plt.tight_layout()
plt.savefig('interconnection_scenario/q2_energy_plus_reserve_by_config_interconnection.png', facecolor=SURFACE)
print('saved q2_energy_plus_reserve_by_config_interconnection.png')
