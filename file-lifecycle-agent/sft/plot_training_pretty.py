"""Slide-ready LoRA training-loss chart from train_log.json (dataviz-skill palette, validated: 4 adjacent slots PASS light).
usage: python plot_training_pretty.py  -> training_loss.png"""
from pathlib import Path
import json
import matplotlib, matplotlib.ticker as mt; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
SURFACE, INK, INK2, MUTED, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#8a8984', '#e6e5e1'
# Fixed categorical order (slot 1..4); the demo model takes slot 1.
RUNS = [('lora_qwen3_1.7b_close', 'dense + close 표시 (시연 모델)', '#2a78d6'),
        ('lora_qwen3_1.7b_dense', 'dense 검색', '#eb6834'),
        ('lora_qwen3_1.7b', 'v1 (단어 검색)', '#1baf7a'),
        ('lora_qwen3_1.7b_pad', '패딩 카탈로그 (데이터 2배)', '#eda100')]
plt.rcParams.update({'font.family': 'AppleGothic', 'axes.unicode_minus': False, 'font.size': 11,
                     'text.color': INK, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2})
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=180); fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
ends = []
for d, label, c in RUNS:
    j = json.loads((HERE / d / 'train_log.json').read_text())
    x = [r['step'] / j['steps'] * 2 for r in j['loss_log']]; y = [r['loss'] for r in j['loss_log']]
    ax.plot(x, y, color=c, lw=1, alpha=0.28, zorder=2)  # raw log points, recessive
    sm = [y[0]]
    for v in y[1:]: sm.append(0.6 * sm[-1] + 0.4 * v)  # EMA in linear space: the trend the eye should follow
    ax.plot(x, sm, color=c, lw=2.2, solid_joinstyle='round', solid_capstyle='round', zorder=3)
    ax.scatter(x[-1:], sm[-1:], s=64, color=c, edgecolors=SURFACE, linewidths=2, zorder=4)  # end-dot with surface ring
    ends.append([sm[-1], label, c, j])
ax.set_yscale('log'); ax.set_ylim(1.5e-4, 0.4); ax.set_xlim(0, 2.95)
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f'{v:g}')); ax.yaxis.set_minor_formatter(mt.NullFormatter())
ax.set_xticks([0, 0.5, 1, 1.5, 2]); ax.set_xlabel('epoch'); ax.set_ylabel('학습 손실 (로그 축)')
ax.grid(axis='y', color=GRID, lw=0.8); ax.tick_params(which='both', length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.axhline(0.4, color=SURFACE)  # keep the top clean
# Direct labels at line ends, spread vertically in log space so they never collide.
import math
ends.sort(key=lambda e: e[0], reverse=True); ly = []
for e in ends:
    v = math.log10(e[0]); v = min(v, ly[-1] - 0.16) if ly else v; ly.append(v)
for (y, label, c, j), v in zip(ends, ly):
    ax.annotate(f'{label} · {round(j["seconds"] / 60)}분', xy=(2, y), xytext=(2.1, 10 ** v), va='center', fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle='-', color=c, lw=1, shrinkA=2, shrinkB=6, relpos=(0, 0.5)))
# One annotation for the takeaway.
ax.annotate('0.25 epoch 만에 0.05 아래로\n→ 도구 호출 형식을 빠르게 익힘', xy=(0.235, 0.04), xytext=(0.55, 0.15), fontsize=10, color=INK2,
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=1))
fig.text(0.06, 0.95, 'Qwen3-1.7B LoRA 학습 손실', fontsize=16, weight='bold', color=INK)
fig.text(0.06, 0.905, 'rank 16 · lr 2e-4 · 2 epoch · A5000  |  진한 선 = 추세(지수이동평균), 흐린 선 = 10 step마다 기록한 원래 값 · 검증 손실은 기록하지 않음', fontsize=10, color=INK2)
fig.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.11)
out = HERE / 'training_loss.png'; fig.savefig(out, facecolor=SURFACE); print(out)
