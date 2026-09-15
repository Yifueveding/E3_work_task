"""
Cumulative NPV by year for the three configurations, extending the Q3c "simple payback"
recommendation to a discounted-cash-flow view.

Assumptions (not given in the exercise inputs, so stated explicitly here, consistent with
the "simple/quick" spirit of the rest of the analysis):
  - Discount rate: 2% (a low-cost-of-capital assumption -- e.g. low-risk infrastructure /
    green-bond financing). Breakeven rates are solar 4.64%, storage (energy-only) 2.64% /
    (with reserve) 3.68%, combined (energy-only) 4.67% / (with reserve) 4.85% -- all above
    2%, so an actual crossing point exists for every configuration to plot. At the more
    typical 4-7% utility WACC, standalone storage never reaches positive NPV at all
    (even with reserve revenue), and solar/combined only cross much later (45-51 years).
  - Analysis horizon: 40 years (long enough for standalone storage, the slowest of the
    three, to cross zero).
  - Revenue = energy (day-ahead, LP multi-cycle base case) + the Q2d illustrative reserve
    scenario (headroom/footroom @ $1.25/MW-hr), held flat in nominal terms, no
    escalation/degradation, no O&M/tax/financing.
  - NPV(year t) = -Capex + sum_{i=1}^{t} Revenue / (1 + r)^i

Caveat: standalone storage's crossing year is genuinely far out (~40 years) -- well beyond
a typical battery's physical/useful life without augmentation. Treat this as illustrating
the discount-rate/revenue sensitivity, not a realistic recommendation on its own.
"""
import matplotlib.pyplot as plt

capex = {'solar': 405_000_000, 'storage': 75_000_000, 'combined': 445_000_000}
energy_revenue = {'solar': 18_803_819, 'storage': 1_977_954, 'combined': 20_791_797}
reserve_revenue = {'solar': 0, 'storage': 781_375, 'combined': 781_875}
revenue = {k: energy_revenue[k] + reserve_revenue[k] for k in capex}

DISCOUNT_RATE = 0.02
YEARS = 40

configs = [
    ('solar', 'Standalone Solar', '#2a78d6'),
    ('storage', 'Standalone Storage', '#eb6834'),
    ('combined', 'Combined Solar + Storage', '#2fa84f'),
]

def npv_series(key, rev, years=YEARS):
    npv = [-capex[key]]
    cross = None
    for t in range(1, years + 1):
        npv.append(npv[-1] + rev / (1 + DISCOUNT_RATE) ** t)
        if cross is None and npv[-1] >= 0:
            cross = t
    return npv, cross

npv_by_year = {}
crossing_year = {}
npv_energy_only = {}
crossing_year_energy_only = {}
for key, _, _ in configs:
    npv_by_year[key], crossing_year[key] = npv_series(key, revenue[key])
    npv_energy_only[key], crossing_year_energy_only[key] = npv_series(key, energy_revenue[key])

print(f'Assumptions: {DISCOUNT_RATE*100:.0f}% discount rate, {YEARS}-year horizon')
print()
def fmt_year(y):
    return f'>{YEARS}' if y is None else str(y)

for key, label, _ in configs:
    print(f'{label}:')
    print(f'  Energy-only:      crosses year {fmt_year(crossing_year_energy_only[key])}, '
          f'NPV@{YEARS}=${npv_energy_only[key][-1]:,.0f}, breakeven rate {100*energy_revenue[key]/capex[key]:.2f}%')
    print(f'  Energy + reserve: crosses year {fmt_year(crossing_year[key])}, '
          f'NPV@{YEARS}=${npv_by_year[key][-1]:,.0f}, breakeven rate {100*revenue[key]/capex[key]:.2f}%')
    print()

INK_PRIMARY, INK_SECONDARY, INK_MUTED = '#0b0b0b', '#52514e', '#898781'
GRIDLINE, BASELINE, SURFACE = '#e1e0d9', '#c3c2b7', '#fcfcfb'

fig, ax = plt.subplots(figsize=(12, 7), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

years_axis = list(range(0, YEARS + 1))
label_offset = {'solar': 1, 'storage': 2, 'combined': 3}
end_labels = []  # (raw_value, text, color, fontsize, alpha, fontweight)
for key, label, color in configs:
    # Energy-only dashed line (skip solar: identical to its solid line, since solar earns $0 reserve)
    if key != 'solar':
        vals_eo = [v / 1e6 for v in npv_energy_only[key]]
        ax.plot(years_axis, vals_eo, color=color, linewidth=1.6, linestyle=(0, (5, 3)), zorder=2, alpha=0.75)
        end_labels.append([vals_eo[-1], f'${vals_eo[-1]:,.0f}M', color, 13, 0.75, 'normal'])
        cy_eo = crossing_year_energy_only.get(key)
        if cy_eo is not None and cy_eo <= YEARS:
            ax.scatter([cy_eo], [0], facecolor='white', edgecolor=color, s=45, zorder=4, linewidth=1.5)

    vals = [v / 1e6 for v in npv_by_year[key]]
    ax.plot(years_axis, vals, color=color, linewidth=2.5, zorder=3, label=label)
    end_labels.append([vals[-1], f'${vals[-1]:,.0f}M', color, 15, 1.0, 'bold'])
    cy = crossing_year.get(key)
    if cy is not None:
        ax.scatter([cy], [0], color=color, s=55, zorder=4, edgecolor='white', linewidth=1)
        y_off = 40 * label_offset[key]
        ax.annotate(f'yr {cy}', xy=(cy, 0), xytext=(cy, y_off),
                    textcoords='data', ha='center', fontsize=13.5, color=color, fontweight='bold',
                    arrowprops=dict(arrowstyle='-', color=color, lw=0.8, alpha=0.6))

# Push overlapping end-of-line labels apart (min separation in data $M units)
MIN_GAP = 30
end_labels.sort(key=lambda r: r[0])
for i in range(1, len(end_labels)):
    if end_labels[i][0] - end_labels[i - 1][0] < MIN_GAP:
        end_labels[i][0] = end_labels[i - 1][0] + MIN_GAP
for y_pos, text, color, fontsize, alpha, weight in end_labels:
    ax.text(YEARS + 0.5, y_pos, text, color=color, fontsize=fontsize, alpha=alpha,
            fontweight=weight, va='center', ha='left')

ax.plot([], [], color=INK_MUTED, linewidth=1.6, linestyle=(0, (5, 3)), alpha=0.75, label='(dashed = energy-only, no reserve)')

ax.axhline(0, color=INK_MUTED, linestyle=(0, (3, 3)), linewidth=1.2, zorder=2)

ax.set_xlim(0, YEARS + 5)
ax.set_xlabel('Project Year', color=INK_PRIMARY, fontsize=13)
ax.set_ylabel('Cumulative NPV ($M)', color=INK_PRIMARY, fontsize=13)
ax.set_title(f'Cumulative NPV by Configuration ({DISCOUNT_RATE*100:.0f}% Discount Rate)',
             color=INK_PRIMARY, fontsize=13.5, fontweight='bold', pad=48, loc='left')
ax.grid(axis='y', color=GRIDLINE, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(BASELINE)
ax.tick_params(axis='y', colors=INK_PRIMARY, length=0, labelsize=13)
ax.tick_params(axis='x', colors=INK_PRIMARY, length=0, labelsize=11)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.01), ncol=2, frameon=False,
          fontsize=10.5, labelcolor=INK_SECONDARY)

fig.text(0.5, 0.005,
          'Solid = energy + reserve; dashed = energy-only (solar omitted — identical to solid). '
          'Storage never reaches positive NPV energy-only within 40 years.',
          color=INK_MUTED, fontsize=9.5, style='italic', ha='center', va='bottom')

plt.tight_layout(rect=[0, 0.035, 1, 1])
plt.savefig('no_interconnection_limit/npv_by_config.png', facecolor=SURFACE)
print('saved npv_by_config.png')
