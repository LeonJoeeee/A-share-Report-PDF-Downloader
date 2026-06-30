# A股财报下载器 (A-share Report Downloader)

从巨潮资讯网（cninfo.com.cn）下载 A 股上市公司原版财报 PDF，并转为 Markdown 供
LLM / agent 分析。本项目是一个 Claude Code 插件，同时也是一个独立 CLI。

## 文件结构

```
├── run.py                           ← skill 调用的自举启动器：首次用自动建 venv 装依赖，再调 cli.py
├── cli.py                           ← 无界面入口。argparse: code period --out --json --no-text --quiet
├── params.py                        ← 参数解析（股票代码校验、季度→报告类型映射），含 QUARTER_CONFIG
├── cninfo.py                        ← 巨潮 API 客户端（查 orgId、搜索公告、拼 PDF 链接、下载）
├── extract.py                       ← PDF → Markdown（pymupdf4llm），仅数字文本 PDF
├── requirements.txt                 ← requests + pymupdf4llm
├── .claude-plugin/plugin.json       ← 插件清单
├── .claude-plugin/marketplace.json  ← marketplace 目录（供 /plugin marketplace add 安装）
└── skills/a-share-report/SKILL.md
```

调用流程（cli.py）：`parse_input` → `get_company_info`（填入真实 org_id）→
`search_announcement` → `build_pdf_url` → `download_pdf` → （默认）`pdf_to_markdown`。

依赖与产物的位置：
- 依赖装在隔离 venv（`$CLAUDE_PLUGIN_DATA/venv`，或独立运行时 `~/.cache/a-share-report-downloader/venv`），
  由 `run.py` 首次运行时自动创建；不进插件代码目录、不污染全局 Python。
- 下载的 PDF / Markdown 存到 `--out` 指定目录（默认当前工作目录），cli.py 输出**绝对路径**；绝不写进插件目录。

## 关键设计决策

### orgId 必须从 API 获取，不能按规律推算

cninfo 内部用数字格式的 orgId（如 `9900024582`），不是 `gssz0{code}` 这种规律。
用 `fulltextSearch/full` 接口通过股票代码查第一条公告，从中取 `orgId` 和 `secName`。
（params.py 里仍保留 `org_prefix` 仅用于交易所判断，不用于拼 orgId。）

### 有效的 cninfo 接口

| 接口 | 用途 | 状态 |
|------|------|------|
| `GET /new/fulltextSearch/full?searchkey={code}` | 查 orgId + 公司名 | ✅ 稳定 |
| `POST /new/hisAnnouncement/query` | 按类型+日期搜索公告列表 | ✅ 稳定 |
| `GET static.cninfo.com.cn/{adjunctUrl}` | 下载 PDF | ✅ 稳定 |
| `GET /new/information/topSearch/detailOfQuery` | 查公司信息 | ❌ 返回 500 |
| `GET /new/information/topSearch/query` | 查公司信息备用 | ❌ 返回 500 |

请求头、超时（10s / 15s / 60s）、POST 表单字段均不可随意改动，已验证可用。

### 季度与报告类型对照

| 用户输入 | cninfo category | 备注 |
|---------|----------------|------|
| Q1 | `category_yjdbg_szsh` | 一季报，搜索范围 1-5 月，year_offset 0 |
| Q2 | `category_bndbg_szsh` | 半年报，搜索 6-9 月，year_offset 0 |
| Q3 | `category_sjdbg_szsh` | 三季报，搜索 9-11 月，year_offset 0 |
| Q4 | `category_ndbg_szsh`  | 年报，次年 1-4 月披露，搜索次年 1-5 月，year_offset 1 |

### 公告筛选逻辑

搜索结果排除含以下关键词的公告：`摘要`、`更正`、`补充`、`英文`、`取消`。
优先选标题里包含目标年份 + 报告类型关键词（title_keywords）的第一条；
若无精确匹配，则返回结果列表第一条兜底。

### PDF → Markdown

用 `pymupdf4llm.to_markdown` 提取。扫描件（无文本层）会得到空白结果，此时 extract.py
抛错，本工具**不做 OCR**。在 cli.py 中提取失败不影响下载：仍退出 0，`text_path` 置 null。

### 退出码

`0` 成功 · `1` 输入/校验错误 · `2` 未找到报告（未披露或报告期有误）· `3` 网络错误。
