---
name: a-share-report
description: Download an A-share (mainland China) listed company's official financial report PDF from cninfo (巨潮资讯网) by 6-digit stock code and report period, then read it as Markdown. Use when the user wants a Chinese listed company's annual report (年报), interim/half-year report (半年报), first-quarter report (一季报), or third-quarter report (三季报) — e.g. "下载 300088 的 2024 年报", "get Luxshare's 2024 half-year report", "拉一下贵州茅台最新季报来分析".
---

# A-share Report Downloader

Downloads an A-share company's official financial report PDF from cninfo
(巨潮资讯网, the SSE/SZSE/BSE-designated disclosure platform) and extracts it to
Markdown so it can be read and analyzed.

## Invocation

```bash
python "${CLAUDE_PLUGIN_ROOT}/run.py" <code> <YYYYQn> --out <dir> [--json]
```

`run.py` is a self-bootstrapping launcher: on first use it creates an isolated
virtualenv and installs the Python dependencies (requests + pymupdf4llm)
automatically — about 30s, once — then runs the downloader. You do NOT need to
pip-install anything by hand, and nothing is installed into the global Python.
(The venv lives in the plugin's persistent data dir, not in the plugin code.)

- `<code>`: 6-digit stock code, e.g. `300088`.
- `<YYYYQn>`: report period, e.g. `2024Q4`.
- `--out <dir>`: where to save the `.pdf` and `.md`. Pass an explicit directory
  in the user's workspace (the current project, or a `reports/` folder). Defaults
  to the current working directory. Files are **never** written into the plugin
  directory.
- `--json`: print one machine-readable JSON object to stdout (recommended — the
  paths are easy to parse). Human progress goes to stderr.
- `--no-text`: download the PDF only, skip Markdown extraction.

Use the literal `${CLAUDE_PLUGIN_ROOT}` env var so the path resolves to the
plugin root wherever it is installed.

## Period mapping

| User intent | Period code |
|-------------|-------------|
| 年报 (annual)        | `Q4` |
| 半年报 (interim)     | `Q2` |
| 一季报 (Q1)          | `Q1` |
| 三季报 (Q3)          | `Q3` |

Example: the 2024 annual report of stock 300088 is `2024Q4`.

## After running

The JSON output's `pdf_path` and `text_path` are absolute paths. Read the
Markdown file (`text_path`) to analyze the report — financials, MD&A, risks,
etc. Tell the user where the files were saved. Prefer `--json` so you can
reliably extract `pdf_path` and `text_path`.

Example JSON stdout:

```json
{"stock_code":"300088","company":"...","period":"2024Q4","report_name":"年报",
 "exchange":"深交所","title":"...","pdf_path":"/abs/...pdf","text_path":"/abs/...md",
 "source_url":"http://static.cninfo.com.cn/..."}
```

## Batch

To fetch several reports, loop the command once per `(code, period)` pair, then
read each resulting `.md`.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success (PDF downloaded; `text_path` may be null if extraction was skipped/failed) |
| 1 | bad input — invalid stock code or period format, or unknown code |
| 2 | report not found — not disclosed yet, or wrong period |
| 3 | network/HTTP error (or automatic dependency setup failed) |

If extraction fails but the PDF downloaded, exit code is still 0 and `text_path`
is null — downloading is the primary job.

## Limitation

Digital-text PDFs only. Scanned reports without a text layer are **not** OCR'd;
for those the PDF is still saved but no Markdown is produced.
