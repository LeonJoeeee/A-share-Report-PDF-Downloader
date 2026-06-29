import os
import threading
import streamlit as st

from utils import parse_input
from fetcher import get_company_info, search_announcement, build_pdf_url
from downloader import download_pdf


def pick_folder() -> str:
    """弹出系统文件夹选择对话框（仅限本地运行）。"""
    import tkinter as tk
    from tkinter import filedialog

    result = [None]

    def _run():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        result[0] = filedialog.askdirectory(title='选择财报保存路径')
        root.destroy()

    t = threading.Thread(target=_run)
    t.start()
    t.join()
    return result[0] or ''


def main():
    st.set_page_config(page_title='A股财报下载', page_icon='📄', layout='centered')
    st.title('A股财报下载器')
    st.caption('数据来源：巨潮资讯网 cninfo.com.cn')

    if 'save_dir' not in st.session_state:
        st.session_state.save_dir = os.path.expanduser('~/Downloads')

    # ── 输入区 ──────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        stock_code = st.text_input('股票代码', placeholder='如 300088', max_chars=6)
    with col2:
        quarter = st.text_input('报告期', placeholder='如 2025Q2')

    st.markdown('**保存路径**')
    path_col, btn_col = st.columns([4, 1])
    with path_col:
        typed_path = st.text_input(
            '路径',
            value=st.session_state.save_dir,
            label_visibility='collapsed',
        )
        st.session_state.save_dir = typed_path
    with btn_col:
        st.write('')  # 对齐垂直位置
        if st.button('📁 浏览'):
            folder = pick_folder()
            if folder:
                st.session_state.save_dir = folder
                st.rerun()

    st.divider()

    # ── 下载按钮 ────────────────────────────────────
    if st.button('下载财报', type='primary', use_container_width=True):
        if not stock_code.strip():
            st.error('请输入股票代码')
            st.stop()
        if not quarter.strip():
            st.error('请输入报告期，如 2025Q2')
            st.stop()

        try:
            params = parse_input(stock_code, quarter)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        status = st.status('正在处理...', expanded=True)

        try:
            with status:
                st.write('查询公司信息...')
                company_name, org_id = get_company_info(params['stock_code'])
                params['org_id'] = org_id
                st.write(f'找到：**{company_name}**（{params["exchange"]}）')

                st.write(f'搜索 {params["year"]}年{params["report_name"]}...')
                ann = search_announcement(params)

                if not ann:
                    status.update(label='未找到报告', state='error')
                    st.error(
                        f'{company_name} {params["year"]}年{params["report_name"]} 暂未找到，'
                        '可能尚未披露或报告期有误'
                    )
                    st.stop()

                title = ann['announcementTitle']
                adjunct_url = ann['adjunctUrl']
                st.write(f'公告标题：{title}')

                st.write('下载 PDF...')
                pdf_url = build_pdf_url(adjunct_url)
                filename = (
                    f"{params['stock_code']}_{company_name}_"
                    f"{params['year']}{params['quarter']}_{params['report_name']}.pdf"
                )
                saved_path = download_pdf(pdf_url, st.session_state.save_dir, filename)

            status.update(label='下载完成', state='complete')
            st.success(f'已保存至：`{saved_path}`')

        except Exception as e:
            status.update(label='出错了', state='error')
            st.error(f'失败：{e}')


if __name__ == '__main__':
    main()
