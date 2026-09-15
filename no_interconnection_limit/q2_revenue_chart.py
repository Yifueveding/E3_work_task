import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Values from q2_revenue.py output (multi-cycle LP dispatch, day-ahead price basis)
solar_rev = 18_803_819
storage_rev = 1_977_954
combined_solar = 18_803_819
combined_storage = 1_987_978
combined_total = combined_solar + combined_storage
standalone_sum = solar_rev + storage_rev

BLUE, ORANGE = '#2a78d6', '#eb6834'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

fig, ax = plt.subplots(figsize=(9, 5.3), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

labels = ['Standalone\nSolar', 'Standalone\nStorage', 'Combined\nSolar + Storage']
x = [0, 1, 2]

# Bar 1: solar only
ax.bar(x[0], solar_rev/1e6, width=0.55, color=BLUE, zorder=3)
# Bar 2: storage only
ax.bar(x[1], storage_rev/1e6, width=0.55, color=ORANGE, zorder=3)
# Bar 3: stacked combined (solar portion + storage portion)
ax.bar(x[2], combined_solar/1e6, width=0.55, color=BLUE, zorder=3, label='Solar revenue component')
ax.bar(x[2], combined_storage/1e6, width=0.55, bottom=combined_solar/1e6, color=ORANGE, zorder=3, label='Storage revenue component')

for xi, val in zip(x, [solar_rev/1e6, storage_rev/1e6, combined_total/1e6]):
    ax.text(xi, val + 0.4, f'${val:.1f}M', ha='center', va='bottom', fontsize=11, color=INK_PRIMARY, fontweight='bold')

ax.set_xticks(x); ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=10.5)
ax.set_ylabel('2023 Backcast Revenue ($M)', color=INK_PRIMARY, fontsize=13)
ax.set_title('2023 Backcast Revenue by Configuration (Day-Ahead Price Basis)',
              color=INK_PRIMARY, fontsize=13, fontweight='bold', pad=14, loc='left')
ax.set_ylim(0, combined_total/1e6 * 1.2)
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top','right','left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)
ax.tick_params(axis='x', length=0)
ax.legend(loc='upper left', frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY, bbox_to_anchor=(0.02, 0.98))

ax.text(2, combined_total/1e6 + 1.6,
        f'vs. sum of standalone: ${standalone_sum/1e6:.2f}M\n(+${(combined_total-standalone_sum):,.0f} interaction benefit, +{100*(combined_total-standalone_sum)/standalone_sum:.2f}%)',
        ha='center', va='bottom', fontsize=8.3, color=INK_MUTED)

plt.tight_layout()
plt.savefig('no_interconnection_limit/q2_revenue_by_config.png', facecolor=SURFACE)
print('saved q2_revenue_by_config.png')
