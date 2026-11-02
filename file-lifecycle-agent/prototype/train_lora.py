"""LoRA SFT for Qwen3 native tool calling. Loss only on the assistant tool call; the prompt is rendered with the same
chat template, tools and enable_thinking=False that QwenToolController uses at inference.
usage: python train_lora.py MODEL_DIR TRAIN_JSONL OUT_DIR [--epochs 2] [--lr 2e-4] [--rank 16]"""
import json, sys, time, random, argparse, math
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
from agent_v5 import SPECS

ap = argparse.ArgumentParser()
ap.add_argument('model'); ap.add_argument('data'); ap.add_argument('out')
ap.add_argument('--epochs', type=int, default=2); ap.add_argument('--lr', type=float, default=2e-4)
ap.add_argument('--rank', type=int, default=16); ap.add_argument('--accum', type=int, default=8); ap.add_argument('--max_len', type=int, default=4096)
a = ap.parse_args()

tok = AutoTokenizer.from_pretrained(a.model)
model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.bfloat16, device_map='cuda')
model.gradient_checkpointing_enable(); model.enable_input_require_grads()
model = get_peft_model(model, LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.05, task_type='CAUSAL_LM',
                                         target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']))
model.print_trainable_parameters()


def encode(row):
    prompt = tok.apply_chat_template(row['messages'], tools=SPECS, add_generation_prompt=True, enable_thinking=False, tokenize=False)
    # Same text the Qwen3 template renders for an assistant tool call; parse() in qwen_tool_controller reads it back.
    target = '<tool_call>\n' + json.dumps(row['call'], ensure_ascii=False) + '\n</tool_call><|im_end|>'
    p, t = tok(prompt, add_special_tokens=False)['input_ids'], tok(target, add_special_tokens=False)['input_ids']
    return (p + t, [-100] * len(p) + t) if len(p) + len(t) <= a.max_len else None


rows = [json.loads(l) for l in open(a.data)]
data = [x for x in map(encode, rows) if x]
print(f'{len(data)}/{len(rows)} examples within {a.max_len} tokens; mean length {sum(len(x[0]) for x in data) / len(data):.0f}', flush=True)
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=a.lr, weight_decay=0.0)
steps = math.ceil(len(data) * a.epochs / a.accum); sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1, (s + 1) / 10) * max(0.0, 1 - s / steps))
rng = random.Random(0); model.train(); step = 0; t0 = time.time(); log = []
for ep in range(a.epochs):
    rng.shuffle(data); run_loss = 0
    for i, (ids, labels) in enumerate(data):
        ids_t = torch.tensor([ids], device='cuda'); lab_t = torch.tensor([labels], device='cuda')
        loss = model(input_ids=ids_t, labels=lab_t).loss / a.accum; loss.backward(); run_loss += loss.item()
        if (i + 1) % a.accum == 0 or i == len(data) - 1:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad(); step += 1
            if step % 10 == 0:
                print(f'epoch {ep} step {step}/{steps} loss {run_loss / 10:.4f} {time.time() - t0:.0f}s', flush=True)
                log.append({'epoch': ep, 'step': step, 'loss': run_loss / 10}); run_loss = 0
model.save_pretrained(a.out)
json.dump({'args': vars(a), 'examples': len(data), 'steps': step, 'seconds': round(time.time() - t0), 'loss_log': log}, open(f'{a.out}/train_log.json', 'w'), indent=1)
print('saved', a.out, flush=True)
