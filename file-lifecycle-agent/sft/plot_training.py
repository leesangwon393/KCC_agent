"""Training curves of the LoRA adapters from train_log.json: TensorBoard event files (sft/tb_logs) and a PNG for slides.
usage: python plot_training.py   then   tensorboard --logdir sft/tb_logs"""
from pathlib import Path
import json
import matplotlib, matplotlib.ticker; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torch.utils.tensorboard import SummaryWriter

HERE = Path(__file__).parent
RUNS = {'lora_qwen3_1.7b': 'v1 (lexical search)', 'lora_qwen3_1.7b_dense': 'dense search', 'lora_qwen3_1.7b_close': 'dense + close flag (demo)', 'lora_qwen3_1.7b_pad': 'padded catalogs'}
plt.rcParams['font.family'] = 'AppleGothic'; plt.rcParams['axes.unicode_minus'] = False
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
for d, label in RUNS.items():
    j = json.loads((HERE / d / 'train_log.json').read_text())
    w = SummaryWriter(HERE / 'tb_logs' / d)
    for r in j['loss_log']: w.add_scalar('train/loss', r['loss'], r['step'])
    w.add_text('config', json.dumps({**j['args'], 'examples': j['examples'], 'seconds': round(j['seconds'])}, ensure_ascii=False)); w.close()
    s = [r['step'] for r in j['loss_log']]; l = [r['loss'] for r in j['loss_log']]
    # x as fraction of training so 1-epoch-size and 2x-size (padded) runs line up
    for a in ax: a.plot([x / j['steps'] * 2 for x in s], l, marker='o', ms=3, label=f"{label} · {j['examples']} ex · {round(j['seconds']/60)}분")
ax[0].set_title('학습 손실 (선형)'); ax[1].set_title('학습 손실 (로그)'); ax[1].set_yscale('log'); ax[1].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:g}'))
for a in ax: a.set_xlabel('epoch'); a.set_ylabel('train loss'); a.grid(alpha=.3)
ax[1].legend(fontsize=8)
fig.suptitle('Qwen3-1.7B LoRA SFT (rank 16, lr 2e-4, 2 epochs, A5000) — 검증 손실은 기록하지 않음')
fig.tight_layout(); fig.savefig(HERE / 'training_curves.png', dpi=160); print(HERE / 'training_curves.png')
