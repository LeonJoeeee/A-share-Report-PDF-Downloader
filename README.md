# A-share Report Downloader · A股财报下载器

Download A-share (mainland China) listed companies' **official** financial
report PDFs from [巨潮资讯网 cninfo.com.cn](http://www.cninfo.com.cn) by stock
code + report period, and extract them to Markdown for LLM/agent analysis.

This project is **both** a Claude Code plugin (exposing an `a-share-report`
skill) and a standalone command-line tool.

## What it is

Give it a 6-digit stock code (e.g. `300088`) and a report period (e.g.
`2024Q4`). It:

1. resolves the company name + cninfo internal `orgId` via the official search API,
2. finds the matching disclosure announcement (annual / interim / quarterly),
3. downloads the original report PDF, and
4. (by default) converts it to a `.md` text file so an agent can read it.

Data source: [巨潮资讯网 cninfo.com.cn](http://www.cninfo.com.cn) — the
SSE / SZSE / BSE designated information-disclosure platform.

## Requirements

- **Python 3.8+** on the PATH.
- Runs on **Linux, macOS, and Windows** — pure Python plus `requests` and
  `pymupdf4llm` (PyMuPDF publishes prebuilt wheels for all three). As a plugin
  these are installed automatically (below), and the launcher handles per-OS
  virtualenv paths.
- Optional: if **Tesseract OCR** is installed on the system, image-only pages
  are additionally OCR'd. Without it, digital-text pages are still extracted.

## Install as a Claude Code plugin

In Claude Code, add this repo as a plugin marketplace and install the plugin:

```text
/plugin marketplace add Kiamutz/A-share-Report-PDF-Downloader
/plugin install a-share-report-downloader@a-share
```

That's it — no manual dependency setup. The skill calls a self-bootstrapping
launcher (`run.py`) that, on first use, creates an **isolated virtualenv** and
installs the Python dependencies (`requests` + `pymupdf4llm`) automatically
(~30s, once). Nothing is installed into your global Python.

Once installed, the **`a-share-report`** skill triggers when you ask for an
A-share company's official report, e.g. "下载 300088 的 2024 年报" or "拉一下贵州茅台
最新季报来分析".

### Where files go

- **Downloaded report (PDF + `.md`)** → the `--out` directory, which defaults to
  your current working directory (your project). They are **never** saved inside
  the plugin directory. The tool reports absolute paths.
- **Auto-installed dependencies (venv)** → `$CLAUDE_PLUGIN_DATA/venv` (Claude
  Code's persistent plugin-data dir), or a per-user cache dir when run standalone
  (`~/.cache/...` on Linux/macOS, `%LOCALAPPDATA%\...` on Windows) — also outside
  the plugin code directory.

## Standalone CLI usage

No install step needed — `run.py` bootstraps its own deps on first run:

```bash
# 2024 annual report (年报) of 300088, saved into ./reports
python run.py 300088 2024Q4 --out ./reports

# 2024 half-year report (半年报), machine-readable JSON to stdout
python run.py 300088 2024Q2 --json
```

If you'd rather manage the environment yourself, install the deps and call
`cli.py` directly:

```bash
pip install -r requirements.txt
python cli.py 300088 2024Q4 --out ./reports --json
```

Human progress messages go to **stderr**; with `--json` a single JSON object is
printed to **stdout** with keys: `stock_code`, `company`, `period`,
`report_name`, `exchange`, `title`, `pdf_path`, `text_path`, `source_url`
(paths are absolute).

### Period format

`YYYYQn`, where the quarter maps to a report type:

| Period | Report |
|--------|--------|
| `Q1` | 一季报 (first quarter) |
| `Q2` | 半年报 (interim / half-year) |
| `Q3` | 三季报 (third quarter) |
| `Q4` | 年报 (annual) |

### Exit codes

`0` success · `1` bad input (invalid code/period, or unknown code) · `2` report
not found (not disclosed yet / wrong period) · `3` network error.

## Limitation

Digital-text PDFs are always extracted. Scanned reports without a text layer are
OCR'd only if **Tesseract** is installed on the system; otherwise the PDF is
still saved but no Markdown is produced.

## File structure

```
├── run.py                          # self-bootstrapping launcher (the skill calls this)
├── cli.py                          # headless entry point (download + extract)
├── params.py                       # input parsing: code validation + quarter mapping
├── cninfo.py                       # cninfo HTTP client (search + download)
├── extract.py                      # PDF -> Markdown via pymupdf4llm
├── requirements.txt                # requests + pymupdf4llm
├── .claude-plugin/plugin.json      # plugin manifest
├── .claude-plugin/marketplace.json # marketplace catalog (for /plugin marketplace add)
└── skills/a-share-report/SKILL.md
```
