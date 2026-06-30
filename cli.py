#!/usr/bin/env python3
"""Headless entry point for the A-share report downloader.

Downloads an A-share listed company's official financial report PDF from cninfo
(巨潮资讯网) given a 6-digit stock code and a report period (e.g. 2024Q4), then
(by default) extracts it to Markdown for LLM/agent analysis.

Run directly with no install:
    python /abs/path/to/cli.py 300088 2024Q4 --out ./reports --json

Sibling imports (params/cninfo/extract) work because Python puts the script's
directory on sys.path when invoked as `python cli.py`.

Exit codes:
    0  success (PDF downloaded; extraction may have been skipped/failed)
    1  input/validation error (bad code or period)
    2  report not found (not disclosed yet or wrong period)
    3  network/HTTP error
"""

import argparse
import json
import sys

from params import parse_input
from cninfo import (
    get_company_info,
    search_announcement,
    build_pdf_url,
    download_pdf,
)
from extract import pdf_to_markdown

# requests is a hard dependency (declared in requirements.txt and already imported
# by cninfo above). Use its exception base to classify network failures.
import requests
_REQUESTS_EXC = (requests.exceptions.RequestException,)


def _eprint(msg: str, quiet: bool = False) -> None:
    """Progress messages go to stderr so --json stdout stays clean."""
    if not quiet:
        print(msg, file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog='cli.py',
        description=(
            "Download an A-share company's official financial report PDF from "
            'cninfo (巨潮资讯网) and extract it to Markdown.'
        ),
    )
    parser.add_argument('code', help='6-digit stock code, e.g. 300088')
    parser.add_argument('period', help='report period, e.g. 2024Q4 '
                                       '(Q1 一季报 / Q2 半年报 / Q3 三季报 / Q4 年报)')
    parser.add_argument('--out', default='.', help='output directory (default: .)')
    parser.add_argument('--no-text', action='store_true',
                        help='skip PDF -> Markdown extraction (extraction is ON by default)')
    parser.add_argument('--json', action='store_true',
                        help='print a single machine-readable JSON object to stdout')
    parser.add_argument('--quiet', action='store_true',
                        help='suppress human progress messages on stderr')
    args = parser.parse_args(argv)

    quiet = args.quiet

    # 1. Parse & validate input.
    try:
        params = parse_input(args.code, args.period)
    except ValueError as e:
        _eprint(f'输入错误：{e}', quiet)
        return 1

    # 2. Resolve company name + real org_id from the API.
    try:
        _eprint('查询公司信息...', quiet)
        company_name, org_id = get_company_info(params['stock_code'])
        params['org_id'] = org_id
    except _REQUESTS_EXC as e:
        # requests.exceptions.JSONDecodeError (a ValueError subclass) lands here
        # too — a non-JSON cninfo response is a server/network problem, not bad input.
        _eprint(f'网络错误：{e}', quiet)
        return 3
    except ValueError as e:
        # genuine bad input, e.g. unknown stock code
        _eprint(f'输入错误：{e}', quiet)
        return 1

    _eprint(f'找到：{company_name}（{params["exchange"]}）', quiet)

    # 3. Search for the target announcement.
    try:
        _eprint(f'搜索 {params["year"]}年{params["report_name"]}...', quiet)
        ann = search_announcement(params)
    except _REQUESTS_EXC as e:
        _eprint(f'网络错误：{e}', quiet)
        return 3

    if not ann:
        _eprint(
            f'未找到 {company_name} {params["year"]}年{params["report_name"]}'
            '（可能尚未披露或报告期有误）',
            quiet,
        )
        return 2

    title = ann.get('announcementTitle', '')
    adjunct_url = ann.get('adjunctUrl')
    if not adjunct_url:
        _eprint(
            f'未找到可下载的 {company_name} {params["year"]}年{params["report_name"]} '
            'PDF（公告缺少附件链接）',
            quiet,
        )
        return 2
    _eprint(f'公告标题：{title}', quiet)

    # 4. Build URL & download the PDF (the primary job).
    pdf_url = build_pdf_url(adjunct_url)
    filename = (
        f"{params['stock_code']}_{company_name}_"
        f"{params['year']}{params['quarter']}_{params['report_name']}.pdf"
    )
    try:
        _eprint('下载 PDF...', quiet)
        pdf_path = download_pdf(pdf_url, args.out, filename)
    except _REQUESTS_EXC as e:
        _eprint(f'网络错误：{e}', quiet)
        return 3

    _eprint(f'已保存 PDF：{pdf_path}', quiet)

    # 5. Optionally extract to Markdown. Extraction failure does NOT fail the run.
    text_path = None
    if not args.no_text:
        try:
            _eprint('提取 Markdown...', quiet)
            text_path = pdf_to_markdown(pdf_path)
            _eprint(f'已保存 Markdown：{text_path}', quiet)
        except Exception as e:
            _eprint(f'警告：Markdown 提取失败：{e}', quiet)
            text_path = None

    # 6. Emit result.
    if args.json:
        result = {
            'stock_code': params['stock_code'],
            'company': company_name,
            'period': f"{params['year']}{params['quarter']}",
            'report_name': params['report_name'],
            'exchange': params['exchange'],
            'title': title,
            'pdf_path': pdf_path,
            'text_path': text_path,
            'source_url': pdf_url,
        }
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f'{company_name} {params["year"]}年{params["report_name"]} 下载完成')
        print(f'  PDF : {pdf_path}')
        if text_path:
            print(f'  文本: {text_path}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
