"""
Visualizes the tradeoff documented in README.md: the 150 MW POI limit makes the ENERGY
interaction benefit much larger, while simultaneously making the RESERVE contribution
smaller -- both draw on the same underlying physical capacity (storage power rating and
shared export headroom), so a scenario that helps one revenue stream can hurt the other.
"""
import matplotlib.pyplot as plt

# Energy interaction benefit, % (interconnection_analysis.py)
energy_benefit_pct = {'No POI Limit': 0.0482, '150 MW POI Limit': 7.71}

# Combined reserve revenue, $ (interconnection_reserve_scenario.py / no_interconnection_limit/q2_reserve_scenario.py)
reserve_revenue = {'No POI Limit': 781_875, '150 MW POI Limit': 494_824}

BLUE, ORANGE, GREEN, RED = '#2a78d6', '#eb6834', '#2fa84f', '#c0392b'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

labels = ['No POI Limit', '150 MW POI Limit']
x = [0, 1]

fig, axes = plt.subplots(1, 2, figsize=(11, 5.6), dpi=200)
fig.patch.set_facecolor(SURFACE)

# ---------- Panel 1: Energy interaction benefit (grows) ----------
ax = axes[0]
ax.set_facecolor(SURFACE)
vals = [energy_benefit_pct[l] for l in labels]
bars = ax.bar(x, vals, width=0.55, color=[BLUE, GREEN], zorder=3)
ymax = max(vals) * 1.35
ax.set_ylim(0, ymax)
for xi, v in zip(x, vals):
    ax.text(xi, v + ymax * 0.02, f'+{v:.2f}%', ha='center', va='bottom', fontsize=12, color=INK_PRIMARY, fontweight='bold')
ax.annotate('', xy=(1, vals[1] + ymax * 0.14), xytext=(0, vals[0] + ymax * 0.14),
            arrowprops=dict(arrowstyle='-|>', color=GREEN, lw=2))
ax.text(0.5, max(vals) + ymax * 0.2, 'grows sharply', ha='center', va='bottom',
        fontsize=11, color=GREEN, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=10.5)
ax.set_ylabel('Energy Interaction Benefit (%)', color=INK_PRIMARY, fontsize=13)
ax.set_title('Energy: Interaction Benefit', color=INK_PRIMARY, fontsize=13, fontweight='bold', pad=12, loc='left')
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)
ax.tick_params(axis='x', length=0)

# ---------- Panel 2: Combined reserve revenue (shrinks) ----------
ax = axes[1]
ax.set_facecolor(SURFACE)
vals = [reserve_revenue[l] / 1e6 for l in labels]
bars = ax.bar(x, vals, width=0.55, color=[BLUE, RED], zorder=3)
ymax = max(vals) * 1.35
ax.set_ylim(0, ymax)
for xi, v in zip(x, vals):
    ax.text(xi, v + ymax * 0.02, f'${v:.2f}M', ha='center', va='bottom', fontsize=12, color=INK_PRIMARY, fontweight='bold')
ax.annotate('', xy=(1, vals[1] + ymax * 0.14), xytext=(0, vals[0] + ymax * 0.14),
            arrowprops=dict(arrowstyle='-|>', color=RED, lw=2))
ax.text(0.5, max(vals) + ymax * 0.2, '−36.7%', ha='center', va='bottom',
        fontsize=11, color=RED, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=10.5)
ax.set_ylabel('Combined Reserve Revenue ($M)', color=INK_PRIMARY, fontsize=13)
ax.set_title('Reserve: Combined Revenue', color=INK_PRIMARY, fontsize=13, fontweight='bold', pad=12, loc='left')
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)
ax.tick_params(axis='x', length=0)

fig.suptitle('The Interconnection Limit Trades Reserve Value for Energy Value',
             x=0.02, y=0.99, ha='left', fontsize=14.5, fontweight='bold', color=INK_PRIMARY)
plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.savefig('interconnection_scenario/interconnection_reserve_tradeoff.png', facecolor=SURFACE)
print('saved interconnection_reserve_tradeoff.png')
