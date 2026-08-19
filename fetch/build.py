# -*- coding: utf-8 -*-
"""抓取 → 归一化 → 生成 data/latest.json、history_index.json、site/data.js。

本地运行：  python fetch/build.py
（设置环境变量 JUHE_KEY 可启用抖音等聚合兜底源）
"""

import json
import os
import datetime

import sources_cn
import sources_global
import categorize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
SITE_DIR = os.path.join(ROOT, "site")
LATEST = os.path.join(DATA_DIR, "latest.json")
# 历史索引写入 site/，因为 GitHub Pages 只发布 site/ 目录，前端需 fetch 它
HISTORY_INDEX = os.path.join(SITE_DIR, "history_index.json")


def _clean(items):
    """分离正常条目与错误标记。"""
    ok, errs = [], []
    for it in items:
        if isinstance(it, dict) and "_error" in it:
            errs.append(it["_error"])
        else:
            ok.append(it)
    return ok, errs


def collect():
    status = {}
    items = []

    # ---- 国内直抓 ----
    cn_map = [
        ("百度", sources_cn.fetch_baidu),
        ("B站", sources_cn.fetch_bilibili),
        ("知乎", sources_cn.fetch_zhihu),
        ("微博", sources_cn.fetch_weibo),
    ]
    for name, fn in cn_map:
        ok, errs = _clean(fn())
        status[name] = "ok" if not errs else f"fail: {errs[0]}"
        items += ok

    # ---- 国内聚合兜底（抖音等）----
    key = os.environ.get("JUHE_KEY", "")
    ok, errs = _clean(sources_cn.fetch_juhe(key))
    if not key:
        status["聚合"] = "no-key（抖音等源缺失，建议配置 JUHE_KEY）"
    else:
        status["聚合"] = "ok" if not errs else f"fail: {errs[0]}"
    items += ok

    # ---- 全球 ----
    gmap = [
        ("Google Trends US", lambda: sources_global.fetch_trends("US")),
        ("Google Trends GB", lambda: sources_global.fetch_trends("GB")),
        ("Google Trends JP", lambda: sources_global.fetch_trends("JP")),
        ("Hacker News", sources_global.fetch_hn),
        ("GDELT", sources_global.fetch_gdelt),
        ("Google News", sources_global.fetch_gnews),
        ("Mastodon", sources_global.fetch_mastodon),
    ]
    for name, fn in gmap:
        ok, errs = _clean(fn())
        status[name] = "ok" if not errs else f"fail: {errs[0]}"
        items += ok

    return items, status


def enrich(items):
    """分类 + 平台内热度归一化评分（0-100）。"""
    for it in items:
        it["category"] = categorize.categorize(it["title"], it["region"])

    by_plat = {}
    for it in items:
        by_plat.setdefault(it["platform"], []).append(it)

    for plat, lst in by_plat.items():
        lst.sort(key=lambda x: (x["heat"] if isinstance(x["heat"], (int, float)) else -1),
                 reverse=True)
        n = len(lst)
        for i, it in enumerate(lst):
            it["score"] = round(100 * (n - i) / n, 1)
    return items


def update_history(items, now):
    date = now.strftime("%Y-%m-%d")
    cn, gl = {}, {}
    for it in items:
        bucket = cn if it["region"] == "cn" else gl
        bucket[it["category"]] = bucket.get(it["category"], 0) + 1
    entry = {"date": date, "cn": cn, "global": gl}

    hist = []
    if os.path.exists(HISTORY_INDEX):
        try:
            with open(HISTORY_INDEX, encoding="utf-8") as f:
                hist = json.load(f)
        except Exception:
            hist = []
    hist = [h for h in hist if h["date"] != date]
    hist.append(entry)
    hist.sort(key=lambda x: x["date"])
    hist = hist[-90:]  # 仅保留近 90 天
    with open(HISTORY_INDEX, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SITE_DIR, exist_ok=True)

    items, status = collect()
    items = enrich(items)

    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "updated_at": now.isoformat(),
        "status": status,
        "count": len(items),
        "items": items,
    }

    with open(LATEST, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    update_history(items, now)

    with open(os.path.join(SITE_DIR, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")

    failed = [k for k, v in status.items() if v.startswith("fail")]
    print(f"[build] items={len(items)} updated={now.isoformat()}")
    print(f"[build] sources: {status}")
    if failed:
        print(f"[build] WARNING 部分源失败: {failed}")


if __name__ == "__main__":
    main()
