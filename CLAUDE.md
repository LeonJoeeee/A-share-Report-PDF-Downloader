# A股财报下载器

从巨潮资讯网（cninfo.com.cn）下载 A 股上市公司原版财报 PDF。

## 文件结构

```
a-report/
├── app.py          ← Streamlit 主界面，启动命令：streamlit run app.py
├── utils.py        ← 参数解析（股票代码校验、季度→报告类型映射）
├── fetcher.py      ← 巨潮 API 查询（获取 orgId、搜索公告、拼接 PDF 链接）
└── downloader.py   ← 下载 PDF 到本地指定路径
```

## 关键设计决策

### orgId 必须从 API 获取，不能按规律推算

cninfo 内部用数字格式的 orgId（如 `9900024582`），不是 `gssz0{code}` 这种规律。
用 `fulltextSearch/full` 接口通过股票代码查第一条公告，从中取 `orgId` 和 `secName`。

### 有效的 cninfo 接口

| 接口 | 用途 | 状态 |
|------|------|------|
| `GET /new/fulltextSearch/full?searchkey={code}` | 查 orgId + 公司名 | ✅ 稳定 |
| `POST /new/hisAnnouncement/query` | 按类型+日期搜索公告列表 | ✅ 稳定 |
| `GET static.cninfo.com.cn/{adjunctUrl}` | 下载 PDF | ✅ 稳定 |
| `GET /new/information/topSearch/detailOfQuery` | 查公司信息 | ❌ 返回 500 |
| `GET /new/information/topSearch/query` | 查公司信息备用 | ❌ 返回 500 |

### 季度与报告类型对照

| 用户输入 | cninfo category | 备注 |
|---------|----------------|------|
| Q1 | `category_yjdbg_szsh` | 截止 4 月 30 日，搜索范围 1-5 月 |
| Q2 | `category_bndbg_szsh` | 半年报，截止 8 月 31 日，搜索 6-9 月 |
| Q3 | `category_sjdbg_szsh` | 截止 10 月 31 日，搜索 9-11 月 |
| Q4 | `category_ndbg_szsh`  | 年报，次年 1-4 月披露，搜索次年 1-5 月 |

### 公告筛选逻辑

搜索结果排除含以下关键词的公告：`摘要`、`更正`、`补充`、`英文`、`取消`
优先选标题里包含目标年份 + 报告类型关键词的第一条。

### 文件夹选择对话框

用 `tkinter.filedialog.askdirectory()` 在独立线程里运行，规避 Streamlit 主线程限制。
仅限本地运行，不支持部署到服务器。
