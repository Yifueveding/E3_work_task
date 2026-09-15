import matplotlib.pyplot as plt

# Values from q2_reserve_scenario.py / q2_revenue.py output ($1.25/MW-hr reserve price, multi-cycle LP dispatch, DA price basis)
energy_rev = {'solar': 18_803_819, 'storage': 1_977_954, 'combined': 20_791_797}
combined_solar_component = 18_803_819
combined_storage_component = 1_987_978  # differs slightly from standalone storage (free clipped-solar charging)
reserve_rev = {'solar': 0, 'storage': 781_375, 'combined': 781_875}

BLUE, ORANGE, GREEN = '#2a78d6', '#eb6834', '#2fa84f'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

labels = ['Standalone\nSolar', 'Standalone\nStorage', 'Combined\nSolar + Storage']
keys = ['solar', 'storage', 'combined']
x = [0, 1, 2]

energy_vals = [energy_rev[k] / 1e6 for k in keys]
reserve_vals = [reserve_rev[k] / 1e6 for k in keys]
totals = [e + r for e, r in zip(energy_vals, reserve_vals)]
YMAX = max(totals) * 1.22  # shared scale across both charts for direct visual comparison


def style_axes(ax, title):
    ax.set_xticks(x); ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=10.5)
    ax.set_ylabel('2023 Backcast Revenue ($M)', color=INK_PRIMARY, fontsize=13)
    ax.set_title(title, color=INK_PRIMARY, fontsize=13, fontweight='bold', pad=14, loc='left')
    ax.set_ylim(0, YMAX)
    ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ['top', 'right', 'left']:
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(BASELINE)
    ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)
    ax.tick_params(axis='x', length=0)


# ---------- Plot 1: Energy-only (solar vs. storage components highlighted) ----------
fig, ax = plt.subplots(figsize=(9, 5.3), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

combined_solar_m = combined_solar_component / 1e6
combined_storage_m = combined_storage_component / 1e6

ax.bar(x[0], energy_vals[0], width=0.55, color=BLUE, zorder=3, label='Solar revenue component')
ax.bar(x[1], energy_vals[1], width=0.55, color=ORANGE, zorder=3, label='Storage revenue component')
ax.bar(x[2], combined_solar_m, width=0.55, color=BLUE, zorder=3)
ax.bar(x[2], combined_storage_m, width=0.55, bottom=combined_solar_m, color=ORANGE, zorder=3)

for xi, e in zip(x, energy_vals):
    ax.text(xi, e + 0.4, f'${e:.1f}M', ha='center', va='bottom', fontsize=11, color=INK_PRIMARY, fontweight='bold')

ax.text(x[2], combined_solar_m / 2, f'${combined_solar_m:.1f}M', ha='center', va='center',
        fontsize=9, color='white', fontweight='bold')
ax.text(x[2], combined_solar_m + combined_storage_m / 2, f'${combined_storage_m:.1f}M', ha='center', va='center',
        fontsize=9, color='white', fontweight='bold')

style_axes(ax, 'Energy-Only Revenue by Configuration (Day-Ahead Price Basis)')
ax.legend(loc='upper left', frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY, bbox_to_anchor=(0.0, 1.06))
plt.tight_layout()
plt.savefig('no_interconnection_limit/q2_energy_only_by_config.png', facecolor=SURFACE)
print('saved q2_energy_only_by_config.png')
plt.close(fig)

# ---------- Plot 2: Energy + Reserve ----------
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

style_axes(ax, 'Energy + Reserve Revenue by Configuration')
ax.legend(loc='upper left', frameon=False, fontsize=9, labelcolor=INK_SECONDARY, bbox_to_anchor=(0.0, 1.05))
plt.tight_layout()
plt.savefig('no_interconnection_limit/q2_energy_plus_reserve_by_config.png', facecolor=SURFACE)
print('saved q2_energy_plus_reserve_by_config.png')
plt.close(fig)
