"""
投资推演模拟 v2
200万总资金，半仓起点（100万/15元已持仓 + 100万现金），30交易日
所有策略均可加仓也可减仓，管理全部200万
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import os, warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 130

OUT = 'docs/public/sim'
os.makedirs(OUT, exist_ok=True)

# ── 初始参数 ────────────────────────────────────────────
P0          = 15.0
INIT_SHARES = 1_000_000 / P0      # 约 66,667 股（已持仓）
INIT_CASH   = 1_000_000            # 现金
TOTAL       = 2_000_000
DAYS        = 30
np.random.seed(42)

# ── 五种价格情景 ────────────────────────────────────────
def make_path(trend_fn, noise=0.30):
    t  = np.arange(DAYS + 1)
    base = np.array([trend_fn(d) for d in t])
    rnd  = np.cumsum(np.random.normal(0, noise, DAYS + 1))
    return np.clip(base + rnd, 5, 45).round(2)

scenarios = {
    'A_持续上涨': {'prob':0.15,'color':'#e74c3c','short':'↑ 持续涨',
        'path': make_path(lambda t: P0 + t*0.28, 0.22)},
    'B_先涨后跌': {'prob':0.25,'color':'#e67e22','short':'↑↓ 先涨后跌',
        'path': make_path(lambda t: P0 + 5*np.sin(t/DAYS*np.pi), 0.28)},
    'C_震荡横盘': {'prob':0.20,'color':'#27ae60','short':'↔ 震荡横盘',
        'path': make_path(lambda t: P0 + 1.5*np.sin(t/4.5), 0.35)},
    'D_先跌后涨': {'prob':0.25,'color':'#3498db','short':'↓↑ 先跌后涨',
        'path': make_path(lambda t: P0 - 5*np.sin(t/DAYS*np.pi), 0.28)},
    'E_持续下跌': {'prob':0.15,'color':'#9b59b6','short':'↓ 持续跌',
        'path': make_path(lambda t: P0 - t*0.25, 0.22)},
}

# ── 五种策略（均可加仓+减仓，管理全部200万）─────────────
def sim(prices, strategy):
    """
    返回 (每日总资产数组, 每日持股数数组, 每日现金数组)
    """
    s  = INIT_SHARES   # 持股数
    c  = INIT_CASH     # 现金
    cost_basis = P0    # 加权平均成本

    equity_hist = [s * prices[0] + c]
    shares_hist = [s]
    cash_hist   = [c]

    for i in range(1, DAYS + 1):
        p     = prices[i]
        p_pre = prices[i-1]
        pct   = (p - p_pre) / p_pre
        total_equity = s * p + c

        if strategy == 'hold':
            # 完全持仓不动
            pass

        elif strategy == 'dca':
            # 等额定投：每天把现金/剩余天数 买入，不主动减仓
            daily = c / (DAYS - i + 1)
            buy   = min(daily, c)
            s    += buy / p
            c    -= buy

        elif strategy == 'momentum':
            # 追涨杀跌：涨>1.5% 追买，跌>1.5% 减仓止损
            if pct > 0.015 and c > 1000:
                buy_amt = min(c, INIT_CASH * 0.12)
                s      += buy_amt / p
                c      -= buy_amt
                cost_basis = (cost_basis * (s - buy_amt/p) + p * (buy_amt/p)) / s if s > 0 else p
            elif pct < -0.015 and s > 0:
                sell_sh = s * 0.10
                s      -= sell_sh
                c      += sell_sh * p

        elif strategy == 'contrarian':
            # 逢跌加仓+高位减仓：跌>2% 加仓，涨>2% 减仓
            if pct < -0.02 and c > 1000:
                buy_amt = min(c, INIT_CASH * 0.15)
                s      += buy_amt / p
                c      -= buy_amt
            elif pct > 0.02 and s > INIT_SHARES * 0.3:
                sell_sh = s * 0.08
                s      -= sell_sh
                c      += sell_sh * p

        elif strategy == 'stoploss':
            # 严格止损止盈：总亏>10%清仓，总盈>20%减半
            pnl_pct = (total_equity - TOTAL) / TOTAL
            if pnl_pct < -0.10 and s > 0:
                c += s * p
                s  = 0.0
            elif pnl_pct > 0.20 and s > 0:
                sell_sh = s * 0.5
                s      -= sell_sh
                c      += sell_sh * p
            elif s == 0 and pnl_pct > -0.05 and c > 0:
                # 止损后企稳再进
                s  = c * 0.5 / p
                c -= s * p

        equity_hist.append(s * p + c)
        shares_hist.append(s)
        cash_hist.append(c)

    return (np.array(equity_hist),
            np.array(shares_hist),
            np.array(cash_hist))

STRATEGIES = {
    'hold':       ('持仓不动（基准）', '#7f8c8d'),
    'dca':        ('DCA 等额定投',     '#27ae60'),
    'momentum':   ('追涨杀跌',         '#e74c3c'),
    'contrarian': ('逢跌加仓/高位减仓','#3498db'),
    'stoploss':   ('止损止盈',         '#e67e22'),
}

days_arr = np.arange(DAYS + 1)

# ══════════════════════════════════════════════════════════
# 图1：五种价格情景
# ══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 4.5))
for sc in scenarios.values():
    ax.plot(days_arr, sc['path'], color=sc['color'], lw=2.2,
            label=f"{sc['short']} ({sc['prob']*100:.0f}%)")
ax.axhline(P0, color='gray', ls='--', lw=1.2, label=f'建仓成本 {P0}元')
ax.set_title('五种价格情景路径（30个交易日）', fontsize=13, fontweight='bold')
ax.set_xlabel('交易日'); ax.set_ylabel('股价（元）')
ax.legend(fontsize=9, loc='upper left'); ax.grid(alpha=0.2)
plt.tight_layout()
plt.savefig(f'{OUT}/fig1_scenarios.png', bbox_inches='tight')
plt.close(); print('✓ fig1')

# ══════════════════════════════════════════════════════════
# 图2：各情景×各策略 总资产演变（5×1 子图）
# ══════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
axes_flat = axes.flatten()

for idx, (sc_key, sc) in enumerate(scenarios.items()):
    ax  = axes_flat[idx]
    ax2 = ax.twinx()
    ax2.plot(days_arr, sc['path'], color='#bdc3c7', lw=1.2, ls='--')
    ax2.set_ylabel('股价（元）', fontsize=7, color='#95a5a6')
    ax2.tick_params(axis='y', labelsize=6.5, colors='#95a5a6')
    ax2.set_ylim(sc['path'].min()*0.85, sc['path'].max()*1.15)

    for st_key, (st_name, st_color) in STRATEGIES.items():
        eq, _, _ = sim(sc['path'], st_key)
        ax.plot(days_arr, eq/10000, color=st_color, lw=1.9, label=st_name)

    ax.axhline(TOTAL/10000, color='black', lw=0.7, ls=':', alpha=0.4)
    ax.set_title(f"{sc['short']}  概率{sc['prob']*100:.0f}%",
                 fontsize=10, fontweight='bold', color=sc['color'])
    ax.set_xlabel('交易日', fontsize=7.5)
    ax.set_ylabel('总资产（万元）', fontsize=7.5)
    ax.tick_params(labelsize=7); ax.grid(alpha=0.18)
    if idx == 0:
        ax.legend(fontsize=7, loc='lower right')

axes_flat[5].set_visible(False)
fig.suptitle('五种情景下各策略总资产演变（万元）\n半仓起点，加仓/减仓均可操作',
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUT}/fig2_equity.png', bbox_inches='tight')
plt.close(); print('✓ fig2')

# ══════════════════════════════════════════════════════════
# 图3：收益率热力矩阵 + 概率加权期望收益
# ══════════════════════════════════════════════════════════
sc_labels = [sc['short'] for sc in scenarios.values()]
st_keys   = list(STRATEGIES.keys())
st_names  = [STRATEGIES[k][0] for k in st_keys]
probs     = np.array([sc['prob'] for sc in scenarios.values()])

matrix = np.zeros((len(scenarios), len(st_keys)))
for i, (sc_key, sc) in enumerate(scenarios.items()):
    for j, st_key in enumerate(st_keys):
        eq, _, _ = sim(sc['path'], st_key)
        matrix[i, j] = (eq[-1] - TOTAL) / TOTAL * 100

weighted = probs @ matrix

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

im = axes[0].imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=-20, vmax=20)
axes[0].set_xticks(range(len(st_names))); axes[0].set_xticklabels(st_names, fontsize=8.5)
axes[0].set_yticks(range(len(sc_labels))); axes[0].set_yticklabels(sc_labels, fontsize=9)
axes[0].set_title('各情景×策略 总收益率（%）', fontsize=11, fontweight='bold')
for i in range(len(sc_labels)):
    for j in range(len(st_names)):
        v = matrix[i, j]
        axes[0].text(j, i, f'{v:+.1f}%', ha='center', va='center',
                     fontsize=8, color='white' if abs(v)>10 else 'black', fontweight='bold')
plt.colorbar(im, ax=axes[0], shrink=0.85)

colors_bar = [STRATEGIES[k][1] for k in st_keys]
bars = axes[1].bar(st_names, weighted, color=colors_bar, width=0.55, edgecolor='white', lw=1.2)
for bar, v in zip(bars, weighted):
    axes[1].text(bar.get_x()+bar.get_width()/2,
                 v + (0.3 if v >= 0 else -0.7),
                 f'{v:+.2f}%', ha='center',
                 va='bottom' if v >= 0 else 'top', fontsize=9.5, fontweight='bold')
axes[1].axhline(0, color='black', lw=0.8)
axes[1].set_title('概率加权期望收益率', fontsize=11, fontweight='bold')
axes[1].set_ylabel('期望收益率（%）'); axes[1].grid(axis='y', alpha=0.22)
plt.tight_layout()
plt.savefig(f'{OUT}/fig3_heatmap.png', bbox_inches='tight')
plt.close(); print('✓ fig3')

# ══════════════════════════════════════════════════════════
# 图4：追涨杀跌的正确与错误——逐情景验证
# ══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

mom_pcts  = matrix[:, st_keys.index('momentum')]
cont_pcts = matrix[:, st_keys.index('contrarian')]
dca_pcts  = matrix[:, st_keys.index('dca')]
hold_pcts = matrix[:, st_keys.index('hold')]
x = np.arange(len(sc_labels)); w = 0.22

axes[0].bar(x - 1.5*w, hold_pcts,  w, color='#7f8c8d', label='持仓不动', alpha=0.85)
axes[0].bar(x - 0.5*w, dca_pcts,   w, color='#27ae60', label='DCA定投',  alpha=0.85)
axes[0].bar(x + 0.5*w, cont_pcts,  w, color='#3498db', label='逢跌加仓', alpha=0.85)
axes[0].bar(x + 1.5*w, mom_pcts,   w, color='#e74c3c', label='追涨杀跌', alpha=0.85)
axes[0].axhline(0, color='black', lw=0.8)
axes[0].set_xticks(x); axes[0].set_xticklabels(sc_labels, fontsize=8.5)
axes[0].set_ylabel('收益率（%）')
axes[0].set_title('四策略各情景收益率对比', fontsize=11, fontweight='bold')
axes[0].legend(fontsize=8.5); axes[0].grid(axis='y', alpha=0.22)

# 右：追涨杀跌的结论象限
axes[1].set_xlim(0,10); axes[1].set_ylim(0,10)
axes[1].axvline(5, color='#bdc3c7', lw=1.5)
axes[1].axhline(5, color='#bdc3c7', lw=1.5)
axes[1].set_xticks([]); axes[1].set_yticks([])
axes[1].set_xlabel('趋势持续性  弱 ←───────────→ 强', fontsize=9.5)
axes[1].set_ylabel('波动幅度  低 ←───────────→ 高', fontsize=9.5)
axes[1].set_title('追涨杀跌：什么时候对？什么时候错？', fontsize=11, fontweight='bold')

quads = [
    (2.5,7.5,'逢跌加仓最优\n追涨杀跌亏损最多\n（震荡高波动）','#3498db'),
    (7.5,7.5,'追涨杀跌偶尔有效\n但风险极高\n（单边强势+高波动）','#e67e22'),
    (2.5,2.5,'DCA定投稳健\n追涨杀跌中性\n（低波动无方向）','#27ae60'),
    (7.5,2.5,'追涨杀跌收益最高\n（单边上涨/低波动）','#e74c3c'),
]
for qx,qy,txt,c in quads:
    axes[1].add_patch(mpatches.FancyBboxPatch(
        (qx-2.3,qy-1.8),4.6,3.6, boxstyle='round,pad=0.15',
        facecolor=c, alpha=0.15, edgecolor=c, lw=1.2))
    axes[1].text(qx,qy,txt,ha='center',va='center',fontsize=8.5,
                 fontweight='bold',color=c)

sc_pos = [
    ('持续涨',8.2,2.5,'#e74c3c'),
    ('先涨后跌',7,7,'#e67e22'),
    ('震荡',2.5,8,'#27ae60'),
    ('先跌后涨',6.5,7.2,'#3498db'),
    ('持续跌',8,3.2,'#9b59b6'),
]
for nm,px,py,c in sc_pos:
    axes[1].plot(px,py,'o',color=c,ms=8,zorder=5)
    axes[1].text(px+0.25,py+0.3,nm,fontsize=8,color=c,fontweight='bold')

plt.tight_layout()
plt.savefig(f'{OUT}/fig4_verdict.png', bbox_inches='tight')
plt.close(); print('✓ fig4')

# ══════════════════════════════════════════════════════════
# 图5：30天操作节奏（推荐方案）
# ══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

weeks_label = ['第1周\nD1-5','第2周\nD6-10','第3周\nD11-15',
               '第4周\nD16-20','第5周\nD21-25','第6周\nD26-30']
# 推荐节奏：前轻后重，先观察，有条件触发
rec_buy  = [10, 15, 20, 20, 20, 15]   # 万元（买入）
rec_sell = [ 0,  0,  5,  5,  5,  5]   # 万元（减仓，高位时）

x = np.arange(6); w = 0.38
axes[0].bar(x-w/2, rec_buy,  w, color='#27ae60', label='计划加仓（万元）', alpha=0.88)
axes[0].bar(x+w/2, rec_sell, w, color='#e74c3c', label='条件减仓（万元）', alpha=0.88)
for i,(b,s) in enumerate(zip(rec_buy,rec_sell)):
    axes[0].text(i-w/2, b+0.4, f'{b}万', ha='center', fontsize=8.5, fontweight='bold', color='#27ae60')
    if s > 0:
        axes[0].text(i+w/2, s+0.4, f'{s}万', ha='center', fontsize=8.5, fontweight='bold', color='#e74c3c')
axes[0].set_xticks(x); axes[0].set_xticklabels(weeks_label, fontsize=9)
axes[0].set_ylabel('资金量（万元）'); axes[0].grid(axis='y', alpha=0.22)
axes[0].set_title('推荐操作节奏：每周加仓/减仓计划\n（基于概率加权最优方案）', fontsize=10.5, fontweight='bold')
axes[0].legend(fontsize=9.5)

# 右：操作决策树
axes[1].set_xlim(0,10); axes[1].set_ylim(0,10); axes[1].axis('off')
axes[1].set_title('每日操作决策树', fontsize=11, fontweight='bold')

nodes = [
    (5,9.2,'开盘前：看昨日涨跌幅','#2c3e50',10.5),
    (2,7.2,'跌幅 > 2%','#e74c3c',9.5),
    (5,7.2,'±2% 以内','#27ae60',9.5),
    (8,7.2,'涨幅 > 2%','#e74c3c',9.5),
    (2,5.3,'加仓\n按周计划×1.5\n（逢跌加仓）','#3498db',9),
    (5,5.3,'按计划\n等额定投\n（DCA执行）','#27ae60',9),
    (8,5.3,'减仓观察\n已盈利部分\n减10-15%','#e74c3c',9),
    (5,3.2,'触发保护：总亏损>10% → 减仓至两成，等企稳','#c0392b',9),
    (5,1.8,'触发止盈：总盈利>20% → 减仓至五成，锁定收益','#16a085',9),
]
for nx,ny,txt,c,fs in nodes:
    axes[1].text(nx,ny,txt,ha='center',va='center',fontsize=fs,color=c,fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.3',facecolor='white',edgecolor=c,alpha=0.9))

# 连线
for (x1,y1),(x2,y2) in [((5,8.85),(2,7.55)),((5,8.85),(5,7.55)),((5,8.85),(8,7.55)),
                          ((2,6.9),(2,5.75)),((5,6.9),(5,5.75)),((8,6.9),(8,5.75))]:
    axes[1].annotate('',xy=(x2,y2),xytext=(x1,y1),
                     arrowprops=dict(arrowstyle='->',color='gray',lw=1.2))

plt.tight_layout()
plt.savefig(f'{OUT}/fig5_plan.png', bbox_inches='tight')
plt.close(); print('✓ fig5')

# ── 文字汇总 ──────────────────────────────────────────────
print('\n══ 概率加权期望收益 ══')
for k, v in zip(st_keys, weighted):
    print(f'  {STRATEGIES[k][0]:16s}: {v:+.2f}%')

print('\n══ 追涨杀跌 vs 逢跌加仓（各情景最优）══')
for i,(sc_key,sc) in enumerate(scenarios.items()):
    m = matrix[i, st_keys.index('momentum')]
    c2 = matrix[i, st_keys.index('contrarian')]
    best = '追涨杀跌✓' if m == max(matrix[i]) else ('逢跌加仓✓' if c2 == max(matrix[i]) else '其他策略✓')
    print(f'  {sc["short"]:12s}: 追涨杀跌{m:+.1f}% | 逢跌加仓{c2:+.1f}% → {best}')

print('\n所有图表已保存至 docs/public/sim/')
