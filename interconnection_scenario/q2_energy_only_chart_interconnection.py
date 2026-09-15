"""
Same chart type/style as analysis/q2_energy_only_by_config.png (solar vs. storage revenue
components, by configuration), but using the 150 MW interconnection-limit scenario's
numbers instead of the base case (no POI limit) numbers. Values from
interconnection_analysis.py output. Saved separately so the two are easy to compare
side by side; the base-case file is untouched.
"""
import matplotlib.pyplot as plt

# Base case (analysis/q2_revenue.py, no POI limit) for shared y-axis scaling only
BASE_MAX_TOTAL = 20_791_797 / 1e6

# 150 MW interconnection-limit scenario (interconnection_analysis.py output)
solar_150 = 15_701_216
storage_unaffected = 1_977_954
combined_150_solar_component = 14_701_366
combined_150_storage_component = 4_341_051
combined_150_total = combined_150_solar_component + combined_150_storage_component

BLUE, ORANGE = '#2a78d6', '#eb6834'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

labels = ['Standalone\nSolar', 'Standalone\nStorage', 'Combined\nSolar + Storage']
x = [0, 1, 2]

fig, ax = plt.subplots(figsize=(9, 5.3), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

solar_m = solar_150 / 1e6
storage_m = storage_unaffected / 1e6
combined_solar_m = combined_150_solar_component / 1e6
combined_storage_m = combined_150_storage_component / 1e6
combined_total_m = combined_150_total / 1e6

ax.bar(x[0], solar_m, width=0.55, color=BLUE, zorder=3, label='Solar revenue component')
ax.bar(x[1], storage_m, width=0.55, color=ORANGE, zorder=3, label='Storage revenue component')
ax.bar(x[2], combined_solar_m, width=0.55, color=BLUE, zorder=3)
ax.bar(x[2], combined_storage_m, width=0.55, bottom=combined_solar_m, color=ORANGE, zorder=3)

for xi, v in zip(x, [solar_m, storage_m, combined_total_m]):
    ax.text(xi, v + 0.4, f'${v:.1f}M', ha='center', va='bottom', fontsize=11, color=INK_PRIMARY, fontweight='bold')

ax.text(x[2], combined_solar_m / 2, f'${combined_solar_m:.1f}M', ha='center', va='center',
        fontsize=9, color='white', fontweight='bold')
ax.text(x[2], combined_solar_m + combined_storage_m / 2, f'${combined_storage_m:.1f}M', ha='center', va='center',
        fontsize=9, color='white', fontweight='bold')

# Shared y-axis scale with the base-case chart so bar heights are directly comparable
YMAX = max(BASE_MAX_TOTAL, combined_total_m) * 1.22
ax.set_xticks(x); ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=10.5)
ax.set_ylabel('2023 Backcast Revenue ($M)', color=INK_SECONDARY, fontsize=10)
ax.set_title('Energy-Only Revenue by Configuration (150 MW Interconnection Limit)',
              color=INK_PRIMARY, fontsize=13, fontweight='bold', pad=14, loc='left')
ax.set_ylim(0, YMAX)
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='y', colors=INK_MUTED, length=0, labelsize=9)
ax.tick_params(axis='x', length=0)
ax.legend(loc='upper left', frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY, bbox_to_anchor=(0.0, 1.06))

plt.tight_layout()
plt.savefig('interconnection_scenario/q2_energy_only_by_config_interconnection.png', facecolor=SURFACE)
print('saved q2_energy_only_by_config_interconnection.png')
