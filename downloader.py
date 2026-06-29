import os
import re
import requests
from pathlib import Path

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Referer': 'http://www.cninfo.com.cn/',
}


def _safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def download_pdf(url: str, save_dir: str, filename: str) -> str:
    """下载 PDF 到 save_dir/filename，返回完整保存路径。"""
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename)
    if not safe_name.lower().endswith('.pdf'):
        safe_name += '.pdf'
    save_path = os.path.join(save_dir, safe_name)

    resp = requests.get(url, headers=HEADERS, stream=True, timeout=60)
    resp.raise_for_status()

    with open(save_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return save_path
