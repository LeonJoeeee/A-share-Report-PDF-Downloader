"""Input parsing for A-share report lookup.

Ported verbatim (in semantics) from the original utils.py:
- 6-digit stock code validation
- quarter -> cninfo category / report-name / title-keyword / search-range mapping
- exchange (column / org_prefix / exchange-name) detection by code prefix

The returned dict keys are kept identical to the original parse_input so the
rest of the pipeline (cninfo.py) consumes them unchanged.
"""

import re

QUARTER_CONFIG = {
    'Q1': {
        'category': 'category_yjdbg_szsh',
        'report_name': '一季报',
        'title_keywords': ['一季报', '一季度报告'],
        'period_end': '03-31',
        'search_range': ('01-01', '05-31'),
        'year_offset': 0,
    },
    'Q2': {
        'category': 'category_bndbg_szsh',
        'report_name': '半年报',
        'title_keywords': ['半年报', '半年度报告', '中期报告'],
        'period_end': '06-30',
        'search_range': ('06-01', '09-30'),
        'year_offset': 0,
    },
    'Q3': {
        'category': 'category_sjdbg_szsh',
        'report_name': '三季报',
        'title_keywords': ['三季报', '三季度报告'],
        'period_end': '09-30',
        'search_range': ('09-01', '11-30'),
        'year_offset': 0,
    },
    'Q4': {
        'category': 'category_ndbg_szsh',
        'report_name': '年报',
        'title_keywords': ['年度报告', '年报'],
        'period_end': '12-31',
        # 年报在次年1-4月披露
        'search_range': ('01-01', '05-31'),
        'year_offset': 1,
    },
}


def parse_input(code: str, quarter_str: str) -> dict:
    code = code.strip().zfill(6)
    if not re.match(r'^\d{6}$', code):
        raise ValueError('股票代码格式错误，应为6位数字')

    quarter_str = quarter_str.strip().upper()
    m = re.match(r'^(\d{4})(Q[1-4])$', quarter_str)
    if not m:
        raise ValueError('报告期格式错误，请输入如 2025Q2')

    year = int(m.group(1))
    quarter = m.group(2)
    cfg = QUARTER_CONFIG[quarter]

    if code.startswith('6'):
        column, org_prefix, exchange = 'sse', 'gssh0', '上交所'
    elif code.startswith(('4', '8')):
        column, org_prefix, exchange = 'bse', 'gsbj0', '北交所'
    else:
        column, org_prefix, exchange = 'szse', 'gssz0', '深交所'

    search_year = year + cfg['year_offset']
    start_m, end_m = cfg['search_range']

    return {
        'stock_code': code,
        'column': column,
        'org_id': None,  # 由 get_company_info 填入真实值
        'exchange': exchange,
        'category': cfg['category'],
        'report_name': cfg['report_name'],
        'title_keywords': cfg['title_keywords'],
        'year': year,
        'quarter': quarter,
        'period_end': f'{year}-{cfg["period_end"]}',
        'search_start': f'{search_year}-{start_m}',
        'search_end': f'{search_year}-{end_m}',
    }
