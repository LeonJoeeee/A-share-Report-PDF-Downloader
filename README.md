# A-share Report Downloader · A股财报下载器

Download A-share (mainland China) listed companies' **official** financial
report PDFs from [巨潮资讯网 cninfo.com.cn](http://www.cninfo.com.cn) by stock
code + report period, and extract them to Markdown for LLM/agent analysis.

This project is **both** a Claude Code plugin (exposing an `a-share-report`
skill) and a standalone command-line tool — no install step needed to run the
CLI.

## What it is

Give it a 6-digit stock code (e.g. `300088`) and a report period (e.g.
`2024Q4`). It:

1. resolves the company name + cninfo internal `orgId` via the official search API,
2. finds the matching disclosure announcement (annual / interim / quarterly),
3. downloads the original report PDF, and
4. (by default) converts it to a `.md` text file so an agent can read it.

Data source: [巨潮资讯网 cninfo.com.cn](http://www.cninfo.com.cn) — the
SSE / SZSE / BSE designated information-disclosure platform.

## Install as a Claude Code plugin

Add this repository via the `/plugin` command in Claude Code. Once installed it
exposes the **`a-share-report`** skill, which Claude triggers when you ask for an
A-share company's official report (年报 / 半年报 / 一季报 / 三季报).

Install the Python dependencies once:

```bash
pip install -r requirements.txt
```

## Standalone CLI usage

```bash
python cli.py <code> <YYYYQn> [--out DIR] [--json] [--no-text] [--quiet]
```

Examples:

```bash
# 2024 annual report (年报) of 300088, saved into ./reports
python cli.py 300088 2024Q4 --out ./reports

# 2024 half-year report (半年报), machine-readable JSON to stdout
python cli.py 300088 2024Q2 --json
```

Human progress messages go to **stderr**; with `--json` a single JSON object is
printed to **stdout** with keys: `stock_code`, `company`, `period`,
`report_name`, `exchange`, `title`, `pdf_path`, `text_path`, `source_url`.

### Period format

`YYYYQn`, where the quarter maps to a report type:

| Period | Report |
|--------|--------|
| `Q1` | 一季报 (first quarter) |
| `Q2` | 半年报 (interim / half-year) |
| `Q3` | 三季报 (third quarter) |
| `Q4` | 年报 (annual) |

### Output

For each report you get a `<code>_<company>_<period>_<report>.pdf` and, unless
`--no-text` is passed, a sibling `.md` with the same name. Read the `.md` to
analyze the report.

### Exit codes

`0` success · `1` bad input (invalid code/period, or unknown code) · `2` report
not found (not disclosed yet / wrong period) · `3` network error.

## Limitation

Digital-text PDFs only. Scanned reports without a text layer are **not** OCR'd —
the PDF is still saved, but no Markdown is produced.

## File structure

```
├── cli.py                       # headless entry point (used by the skill)
├── params.py                    # input parsing: code validation + quarter mapping
├── cninfo.py                    # cninfo HTTP client (search + download)
├── extract.py                   # PDF -> Markdown via pymupdf4llm
├── requirements.txt             # requests + pymupdf4llm
├── .claude-plugin/plugin.json   # plugin manifest
└── skills/a-share-report/SKILL.md
```
