"""Digest: every few hours, while the user is at the Mac, ask once where the unresolved files go.
The user answers in plain language ("1,2는 강화학습 수업 폴더 새로 만들어서 넣고 3은 취준, 나머지는 그냥 둬").
The model turns the reply into proposals with three tools; nothing changes until the user confirms the preview.
Applying creates the new project folder with a _project.md agent guide, so later files are filed there directly."""
from pathlib import Path
import re, subprocess
from agent_v5 import fn, INSTRUCTION

FILES = {'type': 'array', 'items': {'type': 'integer'}, 'description': 'file numbers from the list'}
SPECS = [
    fn('create_project', 'Create a new project folder when the user asks for one (e.g. "새로 만들어서", "폴더 만들어").',
       {'name': {'type': 'string', 'description': 'folder name the user said'}, 'purpose': {'type': 'string', 'description': "one line in the user's words: what this project/course is"}}, ['name', 'purpose']),
    fn('assign_files', 'Put the numbered files into an existing or newly created project.', {'files': FILES, 'project_id': {'type': 'string'}}, ['files', 'project_id']),
    fn('leave_files', 'Leave the numbered files where they are (user said 그냥 둬, 몰라, 개인 자료 ...).', {'files': FILES}, ['files']),
    fn('done', 'Finish after every instruction in the reply is covered.'),
]
SYSTEM = ('You turn a user\'s short Korean reply into file-organizing proposals. The task lists numbered files and existing projects. '
          'Call one tool per turn: create_project only if the user asks for a new folder, then assign_files with the returned project_id; '
          'assign_files for existing projects; leave_files for files the user wants left alone; then done. "나머지" means every file not yet handled.')
BAD_NAME = re.compile(r'[/\\:]|^\.|\.\.')


class ReplyHost:
    def __init__(self, items, catalog, new_root, reply):
        self.items = {x['n']: x for x in items}; self.catalog = catalog; self.root = Path(new_root).expanduser(); self.reply = reply
        self.new = {}; self.moves = {}; self.left = set(); self.done = False; self.nudged = False

    def _files(self, files):
        if not isinstance(files, list) or not files or not all(isinstance(n, int) for n in files): raise ValueError('files must be a non-empty list of numbers')
        bad = [n for n in files if n not in self.items]
        if bad: raise ValueError(f'unknown file numbers {bad}; valid: {sorted(self.items)}')
        twice = [n for n in files if n in self.moves or n in self.left]
        if twice: raise ValueError(f'files {twice} already handled')
        return files

    def call(self, name, args):
        try:
            if name == 'create_project':
                n, purpose = ' '.join(str(args.get('name', '')).split()), ' '.join(str(args.get('purpose', '')).split())
                if not 1 <= len(n) <= 40 or BAD_NAME.search(n): raise ValueError('name must be 1-40 chars without / \\ : or leading dot')
                if not 4 <= len(purpose) <= 200 or INSTRUCTION.search(purpose): raise ValueError('purpose must be a 4-200 char description')
                if n.replace(' ', '') not in self.reply.replace(' ', ''): raise ValueError('name must be the folder name the user wrote')
                for pid, c in {**self.catalog, **self.new}.items():
                    if c['name'].replace(' ', '') == n.replace(' ', ''): raise ValueError(f'project already exists: {pid}')
                pid = f'NEW_{len(self.new) + 1}'
                self.new[pid] = {'name': n, 'desc': purpose, 'folder': str(self.root / n)}
                return {'project_id': pid, 'folder': str(self.root / n)}
            if name == 'assign_files':
                pid = args.get('project_id')
                if pid not in self.catalog and pid not in self.new: raise ValueError(f'unknown project_id; valid: {sorted({**self.catalog, **self.new})}')
                for n in self._files(args.get('files')): self.moves[n] = pid
                return {'status': 'ok'}
            if name == 'leave_files':
                self.left.update(self._files(args.get('files'))); return {'status': 'ok'}
            if name == 'done':
                if not (self.moves or self.left): raise ValueError('nothing proposed yet')
                rest = sorted(set(self.items) - set(self.moves) - self.left)
                if rest and not self.nudged: self.nudged = True; raise ValueError(f'files {rest} are not handled yet: re-read the reply; call done again if the reply says nothing about them')
                self.done = True; return {'status': 'done', 'unhandled': rest}
            return {'error': f'unknown tool {name}'}
        except ValueError as e:
            return {'error': str(e)}

    def proposal(self):
        used = set(self.moves.values())
        return {'new_projects': {k: v for k, v in self.new.items() if k in used},
                'moves': [{**self.items[n], 'project_id': p} for n, p in sorted(self.moves.items())],
                'leave': [self.items[n] for n in sorted(self.left)]}


def task_text(items, catalog, reply):
    files = '\n'.join(f"{x['n']}. {x['name']} — {x['hint']}" for x in items)
    projects = '\n'.join(f"{k}: {c['name']}" for k, c in catalog.items())
    return f'Files:\n{files}\n\nExisting projects:\n{projects}\n\nUser reply:\n{reply}'


def parse_reply(ctl, items, catalog, new_root, reply, max_steps=12):
    from profile_learn import tool_loop
    host = ReplyHost(items, catalog, new_root, reply); trace = []
    tool_loop(ctl, host, SPECS, SYSTEM, task_text(items, catalog, reply), trace, max_steps, lambda: host.done, thinking=True)
    return host.proposal(), trace


def guide(name, purpose, file_names):
    """_project.md for a folder created from the user's reply: the purpose line is the user's own words."""
    seen = '\n'.join(f'- {f}' for f in file_names)
    return f'# {name}\n{purpose}\n(사용자 답변으로 만든 폴더. 자료가 승인될 때마다 아래에 학습 기록이 쌓입니다.)\n\n처음 들어온 자료:\n{seen}\n'


def user_active(max_idle_s=300):
    """True if the keyboard/mouse was used in the last few minutes (macOS HID idle time)."""
    try: out = subprocess.run(['ioreg', '-c', 'IOHIDSystem'], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired): return True
    m = re.search(r'"HIDIdleTime" = (\d+)', out)
    return not m or int(m.group(1)) / 1e9 < max_idle_s
