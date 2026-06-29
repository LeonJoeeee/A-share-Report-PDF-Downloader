from __future__ import annotations

import requests

BASE_URL = 'http://www.cninfo.com.cn'
STATIC_URL = 'http://static.cninfo.com.cn'

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
