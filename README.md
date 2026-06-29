# A股财报下载器

从巨潮资讯网（cninfo.com.cn）一键下载 A 股上市公司原版财报 PDF。

![界面截图](screenshot.png)

## 功能

- 输入股票代码 + 报告期（如 `300088` + `2024Q4`），自动查找并下载对应财报 PDF
- 支持四个报告期：Q1 一季报、Q2 半年报、Q3 三季报、Q4 年报
- 图形界面，可视化选择保存路径

## 安装

需要 Python 3.8 或以上版本。

```bash
pip install -r requirements.txt
```

## 启动

**方式一：** 双击 `启动.bat`（Windows）

**方式二：** 命令行

```bash
streamlit run app.py
```

启动后浏览器自动打开，默认地址 `http://localhost:8501`。

## 使用方法

1. 输入 6 位股票代码，如 `300088`
2. 输入报告期，如 `2024Q4`（年份 + Q1/Q2/Q3/Q4）
3. 选择保存路径
4. 点击「下载财报」

## 数据来源

[巨潮资讯网](http://www.cninfo.com.cn) — 深交所、上交所官方指定信息披露平台。

## 文件结构

```
├── app.py          # Streamlit 主界面
├── fetcher.py      # 巨潮 API 查询
├── downloader.py   # PDF 下载
├── utils.py        # 参数解析
└── requirements.txt
```
