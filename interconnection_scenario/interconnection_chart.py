import matplotlib.pyplot as plt

# Values from interconnection_analysis.py output
scenarios = [
    ('No Interconnection Limit\n(250 MW inverter only)', 18_803_819 + 1_977_954, 20_791_797),
    ('150 MW Interconnection Limit', 17_679_170, 19_042_417),
]

BLUE, ORANGE = '#2a78d6', '#eb6834'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

fig, ax = plt.subplots(figsize=(9.5, 6.0), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

labels = [s[0] for s in scenarios]
standalone_sums = [s[1] / 1e6 for s in scenarios]
combined_totals = [s[2] / 1e6 for s in scenarios]
x = [0, 1]
width = 0.32

x1 = [xi - width / 2 for xi in x]
x2 = [xi + width / 2 for xi in x]
ax.bar(x1, standalone_sums, width=width, color=BLUE, zorder=3, label='Sum of standalone solar + standalone storage')
ax.bar(x2, combined_totals, width=width, color=ORANGE, zorder=3, label='Combined solar + storage')

ymax = max(combined_totals + standalone_sums) * 1.28
ax.set_ylim(0, ymax)

for xi, v in zip(x1, standalone_sums):
    ax.text(xi, v + ymax * 0.015, f'${v:.2f}M', ha='center', va='bottom', fontsize=10.5, color=INK_PRIMARY, fontweight='bold')
for xi, v in zip(x2, combined_totals):
    ax.text(xi, v + ymax * 0.015, f'${v:.2f}M', ha='center', va='bottom', fontsize=10.5, color=INK_PRIMARY, fontweight='bold')

for xi, s, c in zip(x, standalone_sums, combined_totals):
    pct = 100 * (c - s) / s
    ax.annotate('', xy=(xi + width / 2, c + ymax * 0.06), xytext=(xi - width / 2, s + ymax * 0.06),
                arrowprops=dict(arrowstyle='-', color=ORANGE, lw=1.2))
    ax.text(xi, max(s, c) + ymax * 0.11, f'+{pct:.2f}%\ninteraction benefit', ha='center', va='bottom',
            fontsize=10.5, color=ORANGE, fontweight='bold')

ax.set_xticks(x); ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=11)
ax.set_ylabel('2023 Backcast Revenue ($M)', color=INK_SECONDARY, fontsize=10)
ax.set_title('Interaction Benefit Grows Sharply Under a Binding Interconnection Limit',
              color=INK_PRIMARY, fontsize=13.5, fontweight='bold', pad=44, loc='left')
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='y', colors=INK_MUTED, length=0, labelsize=9)
ax.tick_params(axis='x', length=0)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.01), ncol=2, frameon=False,
          fontsize=9.5, labelcolor=INK_SECONDARY)

plt.tight_layout()
plt.savefig('interconnection_scenario/interconnection_interaction_benefit.png', facecolor=SURFACE)
print('saved interconnection_interaction_benefit.png')
