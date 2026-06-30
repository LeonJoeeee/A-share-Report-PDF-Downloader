"""cninfo (巨潮资讯网) HTTP client.

Merges the original fetcher.py + downloader.py into one module with a single
shared HEADERS dict. The cninfo request flow is hard-won and preserved exactly:

  1. get_company_info  -> (company_name, org_id) via fulltextSearch/full
  2. search_announcement -> the best-matching announcement dict (or None)
  3. build_pdf_url      -> static.cninfo.com.cn/{adjunctUrl}
  4. download_pdf       -> streamed download to a safe filename

KEY: org_id MUST come from the API. cninfo's internal orgId is an opaque numeric
value (e.g. 9900024582), NOT derivable from the stock code by any rule.
"""

from __future__ import annotations

import os
import re
import requests
from pathlib import Path

BASE_URL = 'http://www.cninfo.com.cn'
STATIC_URL = 'http://static.cninfo.com.cn'

# Single shared headers dict (the old code duplicated this across modules).
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Referer': 'http://www.cninfo.com.cn/',
    'Accept': 'application/json, text/plain, */*',
}


def get_company_info(stock_code: str) -> tuple:
    """通过全文搜索接口获取 (company_name, org_id)。
    此接口稳定，且返回的 orgId 是巨潮内部真实值，不能靠规律推算。
    """
    url = f'{BASE_URL}/new/fulltextSearch/full'
    params = {
        'searchkey': stock_code,
        'sdate': '',
        'edate': '',
        'isfulltext': 'false',
        'sortType': 'time',
        'pageNum': 1,
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    for ann in data.get('announcements') or []:
        if ann.get('secCode') == stock_code:
            return ann['secName'], ann['orgId']

    raise ValueError(f'未找到股票代码 {stock_code}，请确认代码是否正确')


def search_announcement(params: dict) -> dict | None:
    """在巨潮资讯搜索目标公告，返回最匹配的一条，找不到返回 None。"""
    url = f'{BASE_URL}/new/hisAnnouncement/query'
    post_data = {
        'stock': f"{params['stock_code']},{params['org_id']}",
        'tabName': 'fulltext',
        'pageSize': '30',
        'pageNum': '1',
        'column': params['column'],
        'category': params['category'],
        'seDate': f"{params['search_start']} ~ {params['search_end']}",
        'isHLtitle': 'true',
    }
    headers = {**HEADERS, 'Content-Type': 'application/x-www-form-urlencoded'}
    resp = requests.post(url, data=post_data, headers=headers, timeout=15)
    resp.raise_for_status()

    announcements = resp.json().get('announcements') or []
    if not announcements:
        return None

    # 排除摘要、更正、补充等非正文版本
    exclude = ['摘要', '更正', '补充', '英文', '取消']
    year_str = str(params['year'])

    for ann in announcements:
        title = ann.get('announcementTitle', '')
        if year_str not in title:
            continue
        if any(kw in title for kw in exclude):
            continue
        if any(kw in title for kw in params['title_keywords']):
            return ann

    # 没有精确匹配时，返回第一条兜底
    return announcements[0]


def build_pdf_url(adjunct_url: str) -> str:
    return f'{STATIC_URL}/{adjunct_url}'


def _safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)


# The PDF stream is a static binary file; send a minimal header set (no JSON
# Accept) — matching the original downloader's intent.
DOWNLOAD_HEADERS = {
    'User-Agent': HEADERS['User-Agent'],
    'Referer': HEADERS['Referer'],
}


def download_pdf(url: str, save_dir: str, filename: str) -> str:
    """下载 PDF 到 save_dir/filename，返回完整保存路径。

    校验响应确实是 PDF（首字节 ``%PDF``）；若巨潮返回的是 HTML 拦截页等非 PDF 内容，
    抛出 RequestException，避免把垃圾内容当成 PDF 存下来再让下游提取莫名其妙地失败。
    """
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename)
    if not safe_name.lower().endswith('.pdf'):
        safe_name += '.pdf'
    save_path = os.path.join(save_dir, safe_name)

    resp = requests.get(url, headers=DOWNLOAD_HEADERS, stream=True, timeout=60)
    resp.raise_for_status()

    chunks = resp.iter_content(chunk_size=8192)
    first = b''
    for first in chunks:
        if first:
            break
    if not first.startswith(b'%PDF'):
        raise requests.exceptions.RequestException(
            f'下载内容不是 PDF（{url}），可能是错误页或链接失效'
        )

    with open(save_path, 'wb') as f:
        f.write(first)
        for chunk in chunks:
            f.write(chunk)

    return save_path
