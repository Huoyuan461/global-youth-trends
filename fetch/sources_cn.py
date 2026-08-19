# -*- coding: utf-8 -*-
"""国内数据源抓取。每个 fetcher 独立容错：失败返回含 _error 的字典列表，不抛异常。"""

import json
import urllib.request
import urllib.error
import urllib.parse

from config import CN_SOURCES, USER_AGENT, HEADERS, parse_heat


def _get(url, headers=None, timeout=15):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def fetch_baidu():
    items = []
    try:
        raw = _get(CN_SOURCES["baidu"])
        data = json.loads(raw)
        content = []
        for card in data.get("data", {}).get("cards", []):
            c = card.get("content") or []
            if c and isinstance(c[0], dict) and c[0].get("content"):
                content = c[0]["content"]
                break
        seen = set()
        for i, it in enumerate(content[:30], 1):
            word = it.get("word")
            if not word or word in seen:
                continue
            seen.add(word)
            items.append({
                "platform": "百度", "region": "cn", "sub_region": "cn", "rank": i,
                "title": word, "url": it.get("url", ""),
                "heat": parse_heat(it.get("index")), "category": None,
            })
    except Exception as e:
        items.append({"_error": f"baidu:{e}"})
    return items


def fetch_bilibili():
    items = []
    try:
        raw = _get(CN_SOURCES["bilibili"], headers={
            "User-Agent": USER_AGENT, "Referer": "https://www.bilibili.com/"})
        data = json.loads(raw)
        if data.get("code") == 0:
            for i, it in enumerate(data["data"]["list"][:20], 1):
                bvid = it.get("bvid")
                items.append({
                    "platform": "B站", "region": "cn", "sub_region": "cn", "rank": i,
                    "title": it.get("title", ""),
                    "url": f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                    "heat": (it.get("stat") or {}).get("view"), "category": None,
                })
    except Exception as e:
        items.append({"_error": f"bilibili:{e}"})
    return items


def fetch_zhihu():
    items = []
    try:
        raw = _get(CN_SOURCES["zhihu"], headers={
            "User-Agent": USER_AGENT, "Referer": "https://www.zhihu.com/",
            "x-requested-with": "fetch"})
        data = json.loads(raw)
        for i, it in enumerate(data.get("data", [])[:30], 1):
            tgt = it.get("target", {}) or {}
            title = (tgt.get("title_area") or {}).get("text") or tgt.get("title", "")
            metrics = (tgt.get("metrics_area") or {}).get("text", "")
            url = (tgt.get("link") or {}).get("url", "")
            if not title:
                continue
            items.append({
                "platform": "知乎", "region": "cn", "sub_region": "cn", "rank": i,
                "title": title, "url": url,
                "heat": parse_heat(metrics), "category": None,
            })
    except Exception as e:
        items.append({"_error": f"zhihu:{e}"})
    return items


def fetch_weibo():
    items = []
    try:
        raw = _get(CN_SOURCES["weibo"], headers={
            "User-Agent": USER_AGENT, "Referer": "https://weibo.com/"})
        data = json.loads(raw)
        for i, it in enumerate(data.get("data", {}).get("realtime", [])[:30], 1):
            word = it.get("word")
            if not word:
                continue
            q = urllib.parse.quote(word)
            items.append({
                "platform": "微博", "region": "cn", "sub_region": "cn", "rank": i,
                "title": word, "url": f"https://s.weibo.com/weibo?q=%23{q}%23",
                "heat": it.get("num"), "category": None,
            })
    except Exception as e:
        items.append({"_error": f"weibo:{e}"})
    return items


def fetch_juhe(key):
    """聚合数据·全网热搜榜。免费 50 次/天，返回全网综合热搜（含抖音/知乎/微博等平台爆款，
    接口本身不细分来源）。无 key 时返回空列表（由状态横幅提示「聚合 未配置」）。"""
    items = []
    if not key:
        return items
    try:
        url = f"{CN_SOURCES['juhe']}?key={key}"
        raw = _get(url)
        data = json.loads(raw)
        if data.get("error_code") == 0:
            result = data.get("result") or {}
            # 接口返回 {"list":[...]}（dict），同时兼容直接返回 list 的情况
            lst = result.get("list") if isinstance(result, dict) else (result or [])
            for i, it in enumerate(lst[:30], 1):
                title = it.get("title") or it.get("keyword")
                if not title:
                    continue
                hot = it.get("hotnum") or it.get("hot")
                items.append({
                    "platform": "聚合·全网热搜",
                    "region": "cn", "sub_region": "cn", "rank": i,
                    "title": title, "url": it.get("url", "") or "",
                    "heat": parse_heat(hot), "category": None,
                })
    except Exception as e:
        items.append({"_error": f"juhe:{e}"})
    return items
