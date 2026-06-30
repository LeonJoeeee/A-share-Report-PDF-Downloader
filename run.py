#!/usr/bin/env python3
"""Self-bootstrapping launcher for the A-share report downloader.

The plugin skill calls THIS file. It guarantees the Python dependencies
(requests + pymupdf4llm) are available, then runs cli.py with the same
arguments — so users never have to install anything by hand.

- Fast path: if the dependencies already import (e.g. you ran
  ``pip install -r requirements.txt``), it just runs cli.py with the current
  interpreter.
- Otherwise it creates an isolated virtualenv once, installs requirements into
  it, and runs cli.py with that venv's Python. Cross-platform; the venv is
  cached so the one-time setup (~30s) happens only on first use.

The venv lives in ``$CLAUDE_PLUGIN_DATA`` when running as a Claude Code plugin
(persists across plugin updates), otherwise under the user cache dir. Nothing is
installed into the user's global Python.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import venv
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUIREMENTS = HERE / 'requirements.txt'
CLI = HERE / 'cli.py'
_DEPS = ('requests', 'pymupdf4llm')


def _deps_present() -> bool:
    return all(importlib.util.find_spec(m) is not None for m in _DEPS)


def _venv_dir() -> Path:
    base = os.environ.get('CLAUDE_PLUGIN_DATA')
    if not base:
        cache = os.environ.get('XDG_CACHE_HOME') or str(Path.home() / '.cache')
        base = str(Path(cache) / 'a-share-report-downloader')
    return Path(base) / 'venv'


def _venv_python(venv_dir: Path) -> Path:
    if os.name == 'nt':
        return venv_dir / 'Scripts' / 'python.exe'
    return venv_dir / 'bin' / 'python'


def _ensure_venv() -> Path:
    venv_dir = _venv_dir()
    python = _venv_python(venv_dir)
    if python.exists():
        return python
    print(
        f'[a-share-report] first run: setting up Python deps in {venv_dir} ...',
        file=sys.stderr,
    )
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    venv.create(venv_dir, with_pip=True)
    subprocess.check_call(
        [str(python), '-m', 'pip', 'install', '-q', '-r', str(REQUIREMENTS)],
        stdout=subprocess.DEVNULL,  # keep pip chatter off our stdout
    )
    print('[a-share-report] environment ready.', file=sys.stderr)
    return python


def main() -> int:
    if _deps_present():
        python = sys.executable
    else:
        try:
            python = str(_ensure_venv())
        except (OSError, subprocess.CalledProcessError) as e:
            print(
                f'[a-share-report] automatic dependency setup failed: {e}\n'
                f'Please install manually:  pip install -r {REQUIREMENTS}',
                file=sys.stderr,
            )
            return 3
    return subprocess.call([python, str(CLI), *sys.argv[1:]])


if __name__ == '__main__':
    sys.exit(main())
