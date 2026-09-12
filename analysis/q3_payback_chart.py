import matplotlib.pyplot as plt

configs = ['Standalone\nSolar', 'Standalone\nStorage', 'Combined\nSolar + Storage']
capex = [405_000_000, 75_000_000, 445_000_000]
revenue = [18_803_819, 1_723_678, 20_535_198]
payback = [c/r for c, r in zip(capex, revenue)]

BLUE = '#2a78d6'
INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

fig, ax = plt.subplots(figsize=(10.5, 4.6), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

y = [2, 1, 0]
bars = ax.barh(y, payback, color=BLUE, height=0.5, zorder=3)

for yi, p, c, r in zip(y, payback, capex, revenue):
    label = f'{p:.0f} yrs  (capex \\${c/1e6:,.0f}M / rev \\${r/1e6:.1f}M/yr)'
    ax.text(p + 1, yi, label, va='center', ha='left', fontsize=9.5, color=INK_PRIMARY)

ax.set_yticks(y); ax.set_yticklabels(configs, color=INK_SECONDARY, fontsize=10.5)
ax.set_xlabel('Simple Payback — Capex ÷ Annual Energy-Only Revenue (years)', color=INK_SECONDARY, fontsize=10)
ax.set_title('Simple Payback by Configuration (Energy-Only Revenue, No Financing/Tax/O&M)',
             color=INK_PRIMARY, fontsize=12.5, fontweight='bold', pad=14, loc='left')
ax.set_xlim(0, max(payback)*1.55)
ax.grid(axis='x', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top','right','left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='x', colors=INK_MUTED, length=0, labelsize=9)
ax.tick_params(axis='y', length=0)

plt.tight_layout()
plt.savefig('analysis/q3_payback_comparison.png', facecolor=SURFACE)
print('saved q3_payback_comparison.png')
