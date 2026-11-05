"""Paper-style pipeline figure -> pipeline.svg (render: Chrome headless, see README)."""
from pathlib import Path
from html import escape

W, H = 1520, 700
out = []
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
C = dict(ink='#1f2328', mute='#59636e', line='#8c959f', panel='#f6f8fa', model='#dbeafe', modelS='#2563eb',
         rule='#eef2f7', guard='#fde7d9', guardS='#c2410c', human='#dcfce7', humanS='#15803d', off='#fafafa')


def box(x, y, w, h, fill='#fff', stroke=C['line'], r=6, dash=None, sw=1.2):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def text(x, y, s, size=13, weight='normal', color=None, anchor='middle', mono=False, italic=False):
    fam = 'Menlo, Consolas, monospace' if mono else FONT
    st = ' font-style="italic"' if italic else ''
    out.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{color or C["ink"]}" text-anchor="{anchor}"{st}>{escape(s)}</text>')


def lines(x, y, rows, size=12, gap=None, **k):
    gap = gap or size * 1.35
    for i, r in enumerate(rows): text(x, y + i * gap, r, size, **k)


def label_box(x, y, w, h, title, rows=(), fill='#fff', stroke=C['line'], tsize=13, rsize=11.5, **k):
    box(x, y, w, h, fill, stroke, **k)
    n = 1 + len(rows); top = y + h / 2 - (n - 1) * 8 + 4
    text(x + w / 2, top, title, tsize, 'bold')
    lines(x + w / 2, top + 17, rows, rsize, color=C['mute'])


def arrow(x1, y1, x2, y2, color=C['ink'], dash=None, label=None, lx=0, ly=-6, sw=1.4):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" marker-end="url(#ah)"{d}/>')
    if label: text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, 11, color=C['mute'], italic=True)


def path(d, color=C['ink'], dash=None, label=None, at=(0, 0)):
    ds = f' stroke-dasharray="{dash}"' if dash else ''
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.4" marker-end="url(#ah)"{ds}/>')
    if label: text(at[0], at[1], label, 11, color=C['mute'], italic=True)


def panel(x, y, w, h, tag, title, fill=C['panel'], dash=None):
    box(x, y, w, h, fill, '#d0d7de', r=10, dash=dash)
    text(x + 14, y + 24, f'({tag})  {title}', 14, 'bold', anchor='start')


# ---------------- (a) trigger ----------------
panel(16, 16, 238, 456, 'a', 'Trigger')
for i, (t, s) in enumerate([('Browser download', '~/Downloads'), ('Mac screenshot', '⌘⇧4 → ~/Desktop'), ('iPhone screenshot', 'Back Tap → iCloud inbox')]):
    label_box(36, 54 + i * 62, 198, 50, t, [s])
box(26, 46, 218, 196, 'none', '#afb8c1', r=8, dash='4 3')
text(143, 260, 'new file detected', 10.5, color=C['mute'], italic=True, anchor='start')
arrow(135, 242, 135, 268)
label_box(32, 272, 206, 110, 'File watcher', ['polls every 2 s', 'waits for a stable size', 'skips partial downloads', 'copies in; original untouched'])
arrow(135, 382, 135, 416)
label_box(32, 416, 206, 44, 'Lifecycle manifest', ['register asset (id, path)'], rsize=11)

# ---------------- (b) perception / routing ----------------
panel(272, 16, 222, 456, 'b', 'Inspect & route')
path('M 238 438 C 258 438, 258 76, 282 76')
label_box(282, 52, 196, 48, 'inspect_file', ['type, size, route'], fill='#fff')
for i, (t, s, f, st) in enumerate([('text', ['read_content (chunks)', 'instruction lines redacted'], '#fff', C['line']),
                                   ('image', ['macOS Vision OCR', '→ handled as text'], '#fff', C['line']),
                                   ('weights', ['never read; metadata only', 'find_related_files'], '#fff', C['line'])]):
    y = 136 + i * 108
    label_box(306, y, 172, 84, t, s, fill=f, stroke=st)
    arrow(292, y + 42, 306, y + 42)
out.append(f'<line x1="292" y1="100" x2="292" y2="{136 + 2 * 108 + 42}" stroke="{C["ink"]}" stroke-width="1.4"/>')

# ---------------- (c) agent loop ----------------
panel(512, 16, 600, 456, 'c', 'Agent loop: one tool call per turn, ≤ 12 calls')
arrow(494, 240, 528, 240)
# hybrid controller
box(528, 52, 252, 404, '#fff', '#d0d7de', r=8)
text(654, 74, 'Hybrid controller', 13.5, 'bold')
label_box(544, 88, 220, 70, 'Rule controller', ['explicit ids, lexical match,', 'related-file owners'], fill=C['rule'])
# diamond
cx, cy = 654, 200
out.append(f'<polygon points="{cx},{cy-26} {cx+70},{cy} {cx},{cy+26} {cx-70},{cy}" fill="#fff" stroke="{C["line"]}" stroke-width="1.2"/>')
text(cx, cy + 4, 'plan reached?', 11.5, 'bold')
arrow(654, 158, 654, 174)
arrow(654, 226, 654, 262, label='no → restart', lx=40, ly=4)
label_box(544, 262, 220, 92, 'Qwen3-1.7B + LoRA', ['native tool calling', 'reads, quotes evidence,', 'writes search queries'], fill=C['model'], stroke=C['modelS'])
path(f'M {cx+70} {cy} L 796 {cy} L 796 47 L 1124 47 L 1124 86 L 1146 86')
text(1000, 42, 'yes: rule decision kept, model not called', 11, color=C['mute'], italic=True)
text(cx + 92, cy - 6, 'yes', 11, color=C['mute'], italic=True)
# tool host
box(812, 52, 284, 404, '#fff', '#d0d7de', r=8)
text(954, 74, 'Tool host (validates every call)', 13.5, 'bold')
tools = ['inspect_file', 'read_content', 'search_projects', 'find_related_files', 'assign_project', 'check_references',
         'preview_plan', 'ask_user', 'finish']
box(826, 86, 120, 196, '#fff', C['line'])
text(886, 104, 'tools', 11.5, 'bold')
lines(886, 124, tools, 10.5, gap=17.5, mono=True)
label_box(956, 86, 126, 92, 'Search', ['bge-m3 dense, top-3', '"close" flag when', 'within margin 0.10'], fill='#fff', rsize=10.5)
box(826, 292, 256, 152, C['guard'], C['guardS'])
text(954, 312, 'Guards (error → fed back)', 12.5, 'bold')
lines(840, 334, ['• evidence must be an exact quote', '• quote must single out one project', '• no instructions from file content',
                 '• read the whole text before asking', '• shared weights → ask', '• repeated / malformed call rejected'], 11, anchor='start', gap=17.5)
text(1016, 140, '', 10)
arrow(764, 300, 826, 300, label='call', ly=-7)
arrow(826, 336, 764, 336, label='result', ly=17)
out.append(f'<line x1="956" y1="190" x2="1082" y2="190" stroke="#fff"/>')
label_box(956, 190, 126, 92, 'Untrusted text', ['redacted, then', 'quoted only from', 'what was read'], fill='#fff', rsize=10.5)

# ---------------- (d) decision & approval ----------------
panel(1130, 16, 374, 456, 'd', 'Decision, approval, execution')
arrow(1096, 150, 1146, 108)
arrow(1096, 330, 1146, 244)
label_box(1146, 56, 342, 100, 'planned', ['project + quoted evidence', 'plan: move / archive / keep', 'archive only for completed projects'], fill='#fff')
label_box(1146, 190, 342, 92, 'waiting_user', ['question + candidate projects', '(e.g. projects flagged "close")'], fill='#fff')
path('M 1488 106 L 1497 106 L 1497 344 L 1488 344')
arrow(1317, 282, 1317, 316)
label_box(1146, 316, 342, 56, 'macOS notification + web UI', ['user approves, or answers the question'], fill=C['human'], stroke=C['humanS'])
arrow(1317, 372, 1317, 400)
label_box(1146, 400, 342, 58, 'Executor (after approval only)', ['move / archive, journaled, one-click undo'], fill='#fff')

# ---------------- (e) offline ----------------
panel(16, 490, 1488, 190, 'e', 'Offline: data, fine-tuning, evaluation', fill=C['off'], dash='6 4')
xs = [36, 300, 564, 852, 1140]
items = [('Case collectors', ['LLM agents write one target file,', 'folder context, project catalog,', 'gold label + evidence']),
         ('Three verifiers', ['label / realism / policy lenses', 'keep · fix · drop per case', 'held-out test set kept apart']),
         ('Oracle trajectories', ['gold path replayed through', 'the real tool host;', 'catalog padded to 8–20 projects']),
         ('LoRA SFT', ['loss on the tool call only', '1,358 turns, rank 16', 'RTX A5000, ~30 min']),
         ('Held-out evaluation', ['75 test cases (66 clean),', '3- and 15-project catalogs;', 'accuracy, wrong assigns, tool metrics'])]
for i, (x, (t, r)) in enumerate(zip(xs, items)):
    w = 248 if i < 4 else 348
    label_box(x, 528, w, 100, t, r, fill='#fff')
    if i < 3: arrow(x + 248, 578, xs[i + 1], 578)
arrow(1100, 578, 1140, 578, dash='4 3')
text(860, 508, 'LoRA adapter', 11, color=C['modelS'], italic=True)
path('M 976 528 C 976 490, 700 500, 700 356', C['modelS'], dash='5 4')
text(1314, 664, 'test batches are never used for training', 11, color=C['mute'], italic=True)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>
<rect width="100%" height="100%" fill="#fff"/>
{chr(10).join(out)}
</svg>'''
Path(__file__).with_name('pipeline.svg').write_text(svg)
print('wrote pipeline.svg')
