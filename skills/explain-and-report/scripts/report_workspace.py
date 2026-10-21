#!/usr/bin/env python3
"""Create/check off-repository report workspaces. Python stdlib only; no Git writes.

This is a cooperative path guard, not a sandbox or a data-loss-prevention scanner.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from datetime import datetime, timezone
import uuid

SKILL_ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.bmp', '.tif', '.tiff', '.svg', '.ico'}

class PolicyError(ValueError):
    pass

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def absolute(path: Path | str) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(path))))

def within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents

def git_environment() -> dict[str, str]:
    # Do not let inherited GIT_DIR/GIT_WORK_TREE redirect read-only inspection.
    return {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}

def git_root(path: Path) -> Path | None:
    p = absolute(path)
    for candidate in (p, *p.parents):
        if (candidate / '.git').exists():
            return candidate.resolve()
        if ((candidate / 'HEAD').is_file() and (candidate / 'objects').is_dir()
                and (candidate / 'refs').is_dir()):
            return candidate.resolve()  # also reject bare repository storage
    return None

def assert_external(path: Path, workspace: Path, skill_root: Path = SKILL_ROOT) -> Path:
    lexical = absolute(path)
    real = lexical.resolve()
    source = absolute(workspace)
    roots = {source, source.resolve(), absolute(skill_root), skill_root.resolve()}
    for candidate in (source, source.resolve()):
        repo = git_root(candidate)
        if repo:
            roots.add(repo)
    for candidate in (lexical, real):
        for root in roots:
            if within(candidate, root):
                raise PolicyError(f'Output is inside source/skill/repository: {candidate} (protected: {root})')
        found = git_root(candidate)
        if found:
            raise PolicyError(f'Output is inside a Git repository: {found}')
    return real

def git_read(repo: Path, *args: str) -> bytes:
    if not shutil.which('git'):
        raise PolicyError('Git exists in the workspace but git executable is unavailable; cannot snapshot/check it.')
    p = subprocess.run(['git', '-C', str(repo), *args], env=git_environment(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    if p.returncode:
        raise PolicyError('Read-only git inspection failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    return p.stdout

def image_changes(workspace: Path) -> dict[str, dict[str, str | None]]:
    repo = git_root(workspace.resolve())
    if repo is None:
        return {}
    names: set[str] = set()
    for args in [('diff', '--name-only', '-z'), ('diff', '--cached', '--name-only', '-z'),
                 ('ls-files', '--others', '--exclude-standard', '-z')]:
        names.update(x.decode('utf-8', 'surrogateescape') for x in git_read(repo, *args).split(b'\0') if x)
    stage = {}
    for entry in git_read(repo, 'ls-files', '--stage', '-z').split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        stage[name.decode('utf-8', 'surrogateescape')] = meta.decode('ascii')
    result = {}
    for name in sorted(names):
        if Path(name).suffix.lower() not in IMAGE_EXT:
            continue
        path = repo / name
        # Never follow repo symlinks to read file content.
        if path.is_symlink():
            working = 'symlink:' + os.readlink(path)
        elif path.is_file() and within(path.resolve(), repo.resolve()):
            working = digest(path)
        else:
            working = None
        result[name] = {'working_sha256': working, 'index_entry': stage.get(name)}
    return result

def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    if os.name == 'posix':
        path.chmod(0o600)

def default_home() -> Path:
    configured = os.environ.get('EXPLAIN_REPORT_HOME')
    if configured:
        root = Path(configured).expanduser()
    else:
        base = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))).expanduser()
        if not base.is_absolute():
            raise PolicyError('XDG_STATE_HOME must be absolute.')
        root = base / 'explain-and-report'
    if not root.is_absolute():
        raise PolicyError('EXPLAIN_REPORT_HOME must be absolute.')
    return root

def init_run(workspace: Path, topic: str, root: Path | None = None) -> Path:
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,47}', topic):
        raise PolicyError('--topic must be a non-sensitive ASCII slug (1–48 lowercase letters/digits/hyphens).')
    original = absolute(workspace)
    if not original.is_dir():
        raise PolicyError('--workspace must be an existing source directory.')
    workspace = git_root(original.resolve()) or original.resolve()
    proposed = Path(root).expanduser() if root is not None else default_home()
    if not proposed.is_absolute():
        raise PolicyError('--root must be an absolute path.')
    assert_external(proposed, original)
    root = assert_external(proposed, workspace)
    before = image_changes(workspace)
    project_name = re.sub(r'[^a-zA-Z0-9_-]+', '-', workspace.name).strip('-')[:28] or 'project'
    project = project_name + '-' + hashlib.sha256(str(workspace).encode()).hexdigest()[:8]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + topic + '-' + uuid.uuid4().hex[:8]
    run = assert_external(root / 'runs' / project / run_id, workspace)
    old_umask = os.umask(0o077)
    try:
        run.mkdir(parents=True, mode=0o700, exist_ok=False)
        for sub in ('delivery', 'figures', 'qa/screenshots', 'publish'):
            (run / sub).mkdir(parents=True, mode=0o700)
        write_json(run / 'manifest.json', {
            'schema_version': 1, 'skill_version': '0.4.1', 'run_id': run_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'run_dir': str(run), 'storage_root': str(root), 'workspace': str(workspace),
            'skill_root': str(SKILL_ROOT), 'topic': topic,
            'git_image_changes_before': before,
            'publication_status': 'not_requested',
            'privacy': 'local_internal_not_automatically_shared'
        })
    finally:
        os.umask(old_umask)
    return run

def load_run(run: Path) -> tuple[Path, dict]:
    lexical = absolute(run)
    # Reject symlink entry points before trusting manifest metadata.
    for item in (lexical, *lexical.parents):
        if item.is_symlink():
            raise PolicyError(f'Symlink run path is not accepted: {item}')
    run = lexical.resolve()
    meta_path = run / 'manifest.json'
    if meta_path.is_symlink():
        raise PolicyError('Symlink manifest is not accepted.')
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    if meta.get('schema_version') != 1 or not isinstance(meta.get('workspace'), str):
        raise PolicyError('Not a recognized report run manifest.')
    if run != Path(meta.get('run_dir', '')).resolve():
        raise PolicyError('Run was moved or manifest path does not match; do not silently rebind it.')
    assert_external(run, Path(meta['workspace']))
    if meta.get('skill_root'):
        assert_external(run, Path(meta['workspace']), Path(meta['skill_root']))
    return run, meta

def check_run(run: Path) -> dict:
    run, meta = load_run(run)
    issues = []
    for directory, dirs, files in os.walk(run, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                issues.append('Symlink in run is prohibited: ' + str(path.relative_to(run)))
            elif name == '.git':
                issues.append('Git marker inside report run: ' + str(path.relative_to(run)))
    current = image_changes(Path(meta['workspace']))
    before = meta.get('git_image_changes_before', {})
    # Disappearing changes may be user actions; report newly changed image candidates only.
    delta = [name for name, value in current.items() if before.get(name) != value]
    if delta:
        issues.append('Repository image candidates changed since init. Inspect without undoing user changes.')
    return {'ok': not issues, 'run_dir': str(run), 'issues': issues,
            'repository_image_candidates': delta,
            'limits': 'Cooperative guard, not DLP. Ignores pre-existing unchanged image changes; does not scan arbitrary Base64.'}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Create a unique off-repository run; print JSON.')
    init.add_argument('--workspace', type=Path, default=Path.cwd())
    init.add_argument('--topic', default='report')
    init.add_argument('--root', type=Path)
    check = sub.add_parser('check', help='Read-only safety checks; does not modify Git or delete files.')
    check.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            run = init_run(args.workspace, args.topic, args.root)
            print(json.dumps({'ok': True, 'run_dir': str(run)}, ensure_ascii=False))
            return 0
        result = check_run(args.run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['ok'] else 1
    except (PolicyError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
