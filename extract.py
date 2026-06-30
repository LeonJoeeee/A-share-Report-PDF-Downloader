"""PDF -> Markdown extraction for agent/LLM consumption.

Uses pymupdf4llm to convert a downloaded report PDF into Markdown text that an
LLM can read and analyze. Digital-text PDFs only; scanned reports without a text
layer are not OCR'd.
"""

from __future__ import annotations

import contextlib
import os
import sys


@contextlib.contextmanager
def _stdout_to_stderr():
    """Send anything written to OS-level stdout (fd 1) to stderr instead.

    PyMuPDF/MuPDF write document-parser and OCR progress messages directly to
    file descriptor 1, bypassing ``sys.stdout``. Redirecting at the fd level
    keeps a caller's stdout clean (e.g. cli.py's single ``--json`` line).
    """
    try:
        sys.stdout.flush()
        saved_fd = os.dup(1)
    except (OSError, ValueError):
        # No usable stdout fd (rare on some Windows / embedded setups) — skip the
        # redirect; extraction still runs (stdout may get a little MuPDF noise).
        yield
        return
    try:
        os.dup2(2, 1)
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved_fd, 1)
        os.close(saved_fd)


def pdf_to_markdown(pdf_path: str, md_path: str | None = None) -> str:
    """Convert ``pdf_path`` to Markdown and write it as UTF-8.

    If ``md_path`` is None it is derived from ``pdf_path`` by replacing the
    extension with ``.md``. Returns the path of the written Markdown file.

    Raises:
        ImportError-derived RuntimeError: when pymupdf4llm is not installed.
        ValueError: when the produced Markdown is empty/whitespace-only, which
            usually means the PDF has no text layer (scanned). OCR is not
            supported.
    """
    try:
        import pymupdf4llm
    except ImportError as e:
        raise RuntimeError(
            'pymupdf4llm 未安装，无法将 PDF 转为 Markdown。'
            "请运行: pip install pymupdf4llm"
        ) from e

    # MuPDF emits parser/OCR progress to fd 1; keep it off the caller's stdout.
    with _stdout_to_stderr():
        md = pymupdf4llm.to_markdown(pdf_path)

    if not md or not md.strip():
        raise ValueError(
            f'未能从 PDF 提取到文本: {pdf_path}。'
            '该 PDF 可能是扫描件（无文本层），本工具不支持 OCR。'
        )

    if md_path is None:
        md_path = os.path.splitext(pdf_path)[0] + '.md'

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md)

    return md_path
