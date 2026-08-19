# 全球 + 中国青年关注榜

一个**零服务器成本**的静态网站，每隔约 3 小时自动采集并展示 **18–30 岁年轻人最关心的话题**，
覆盖**中国 + 全球**三大维度：**社交平台热榜 / 搜索热度趋势 / 行业排行**。

- 国内源：百度热搜、B站热门、知乎热榜、微博热搜、（聚合兜底）抖音等
- 全球源：Google Trends（US/GB/JP）、Hacker News、GDELT、Google News、Mastodon
- 部署：GitHub Pages（免费托管）+ GitHub Actions（定时抓取并自动部署）
- 成本：默认 **≈0 元/月**（付费仅在你主动启用 YouTube 趋势榜 / Reddit 聚合 / GNews 时产生，<¥100/月）

---

## 一、本地运行（先看效果）

```bash
cd global-youth-trends
pip install -r requirements.txt
python fetch/build.py            # 无 JUHE_KEY 时抖音等源会降级，其余正常
# 本地预览（history 图表需经 http 访问，别直接双击 index.html）
cd site && python -m http.server 8000
# 浏览器打开 http://localhost:8000
```

可选：配置聚合数据 key 启用抖音等兜底源

```bash
export JUHE_KEY="你的聚合数据key"
python fetch/build.py
```

运行后生成：
- `data/latest.json` —— 当日全部数据（规范备份，站点不直接读）
- `site/data.js` —— 注入前端的数据（`window.DATA`）
- `site/history_index.json` —— 每日行业分布快照（历史趋势图读取）

---

## 二、上线到 GitHub Pages（一次性设置）

1. **新建仓库**：在 GitHub 新建一个仓库（如 `global-youth-trends`），把本项目文件推上去。
2. **配置密钥**：仓库 `Settings → Secrets and variables → Actions → New repository secret`，
   名称 `JUHE_KEY`，值填聚合数据「全网热搜榜」的 key（不配置也能跑，只是缺抖音等源）。
3. **开启 Pages**：仓库 `Settings → Pages → Build and deployment → Source` 选择 **GitHub Actions**。
4. **触发首次运行**：`Actions → refresh-trends → Run workflow`；之后每 3 小时自动跑。
5. **访问站点**：Pages 部署完成后会给出 `https://<用户名>.github.io/global-youth-trends/`。

> 工作流会先把新数据 `commit` 回仓库，再打包 `site/` 目录部署到 Pages。
> 免费额度 2000 分钟/月，每次约 1–2 分钟 × 8 次/天，完全够用。

---

## 三、自定义

- **刷新频率**：改 `.github/workflows/daily.yml` 里的 cron（UTC）。想每小时就改成
  `0 * * * *`（仍在免费额度内）。
- **全球地区**：在 `fetch/config.py` 的 `TRENDS_GEOS` 增加地区代码（如 `KR` 韩国、`BR` 巴西）。
- **启用付费增强**（默认关）：
  - **YouTube 趋势榜**：申请 YouTube Data API v3 key（免费配额足够），在 `sources_global.py` 加 fetcher。
  - **Reddit 聚合**：用第三方聚合（redditapis.com，约 $0.24/千次）替代已失效的免费 Reddit。
  - **GNews**：替换 Google News RSS 以规避其"仅个人非商业"版权限制（公开站点建议）。
- **LLM 增强分类**：在 `fetch/categorize.py` 接入你已有的 OpenAI 兼容 Key，对低置信词二次分类。

---

## 四、成本与风险

| 项 | 说明 |
|---|---|
| 成本 | ≈0（免费源 + 聚合免费档 50 次/天）。付费项均为可选。 |
| 源失效 | 每个源独立容错；失败源留空 + 顶部"数据延迟"横幅，不整页崩溃。 |
| 限流/IP 封锁 | 知乎/微博需 UA+Referer；抖音默认走聚合；GDELT/Trends 已加间隔。 |
| ⚠️ Google News 版权 | RSS 仅限"个人非商业"，**公开站点有法律风险** → 建议改 GNews 或本站注明 demo。 |
| ⚠️ Reddit | 2026 起匿名 API 已封锁，默认不含；付费聚合可选。 |
| 历史曲线 | `history_index.json` 按天累积，运行数天后趋势才明显。 |
| 密钥安全 | 仅 `JUHE_KEY` 走 repo secret，绝不入代码。 |

---

## 五、目录结构

```
global-youth-trends/
├── .github/workflows/daily.yml   # 定时抓取 + Pages 部署
├── fetch/
│   ├── config.py        # 端点 / 请求头 / 分类词表 / 热度解析
│   ├── sources_cn.py    # 百度/B站/知乎/微博/聚合
│   ├── sources_global.py# Trends/HN/GDELT/News/Mastodon
│   ├── categorize.py    # 关键词→行业
│   └── build.py         # 抓取→归一化→生成 data.js / history_index.json
├── data/latest.json     # 当日全部数据（规范备份）
├── site/
│   ├── index.html  style.css  app.js   # 前端（Chart.js 走 CDN，无构建）
│   ├── data.js                     # 由 build.py 注入 window.DATA
│   └── history_index.json          # 每日快照（历史趋势图读取）
├── requirements.txt   # requests
└── README.md
```
