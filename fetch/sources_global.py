# -*- coding: utf-8 -*-
"""全球数据源抓取。每个 fetcher 独立容错：失败返回含 _error 的字典列表。"""

import json
import time
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import urllib.parse

from config import GLOBAL_SOURCES, TRENDS_GEOS, USER_AGENT, parse_heat

_NS = "{https://schemas.google.com/General/2005}"


def _get(url, headers=None, timeout=20, retries=2):
    """HTTP GET，带指数退避重试。429(限流)/超时/网络抖动自动重试。"""
    h = {"User-Agent": USER_AGENT, "Accept": "application/json, application/xml, */*"}
    if headers:
        h.update(headers)
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429 and attempt < retries:
                time.sleep(3 * (2 ** attempt))
                continue
            raise
        except Exception as e:
            last = e
            if attempt < retries:
                time.sleep(2 * (2 ** attempt))
                continue
            raise
    raise last


def fetch_trends(geo):
    items = []
    try:
        url = GLOBAL_SOURCES["trends"].format(geo=geo)
        raw = _get(url)
        root = ET.fromstring(raw)
        for i, item in enumerate(root.iter("item"), 1):
            title = (item.findtext("title") or "").strip()
            traffic = item.findtext(f"{_NS}approx_traffic") or ""
            news = item.find(f"{_NS}news_item")
            url_ = ""
            if news is not None:
                link = news.find(f"{_NS}news_item_url")
                if link is not None:
                    url_ = link.text or ""
            if not title:
                continue
            items.append({
                "platform": "Google Trends", "region": "global", "sub_region": geo,
                "rank": i, "title": title, "url": url_,
                "heat": parse_heat(traffic), "category": None,
            })
    except Exception as e:
        items.append({"_error": f"trends_{geo}:{e}"})
    return items


def fetch_hn():
    """Hacker News 全球科技/游戏青年向热帖（Algolia 接口，单次请求）。"""
    items = []
    try:
        raw = _get(GLOBAL_SOURCES["hn"])
        data = json.loads(raw)
        for i, h in enumerate(data.get("hits", []), 1):
            title = h.get("title") or h.get("story_title") or ""
            if not title:
                continue
            url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            items.append({
                "platform": "Hacker News", "region": "global", "sub_region": "world",
                "rank": i, "title": title, "url": url,
                "heat": h.get("points"), "category": None,
            })
    except Exception as e:
        items.append({"_error": f"hn:{e}"})
    return items


def fetch_gdelt():
    """GDELT 国际/时政/财经新闻骨架（按主题聚合近期文章）。"""
    items = []
    try:
        params = urllib.parse.urlencode({
            "query": "(theme:ECONOMY OR theme:WORLD OR theme:SCIENCE OR theme:HEALTH)",
            "mode": "ArtList", "maxrecords": "25", "format": "json", "sort": "hybridrel",
        })
        url = GLOBAL_SOURCES["gdelt"] + "?" + params
        raw = _get(url)
        data = json.loads(raw)
        for i, art in enumerate(data.get("articles", [])[:25], 1):
            title = art.get("title", "")
            if not title:
                continue
            items.append({
                "platform": "GDELT", "region": "global", "sub_region": "world",
                "rank": i, "title": title, "url": art.get("url", ""),
                "heat": None, "category": None,
            })
    except Exception as e:
        items.append({"_error": f"gdelt:{e}"})
    return items


def fetch_gnews():
    """Google News RSS（全球综合新闻）。
    注意：Google News RSS 版权仅限'个人非商业'，公开站点有风险，
    建议改用 GNews 付费接口或在本站注明 demo/非商用。"""
    items = []
    try:
        raw = _get(GLOBAL_SOURCES["gnews"])
        root = ET.fromstring(raw)
        for i, item in enumerate(root.iter("item"), 1):
            title = (item.findtext("title") or "").strip()
            link = item.findtext("link") or ""
            if not title:
                continue
            items.append({
                "platform": "Google News", "region": "global", "sub_region": "US",
                "rank": i, "title": title, "url": link,
                "heat": None, "category": None,
            })
    except Exception as e:
        items.append({"_error": f"gnews:{e}"})
    return items


def fetch_mastodon():
    """Mastodon 全球社媒趋势标签（Reddit 免费路径已断后的替代）。"""
    items = []
    try:
        raw = _get(GLOBAL_SOURCES["mastodon"],
                   headers={"Accept": "application/json"})
        data = json.loads(raw)
        for i, it in enumerate(data[:20], 1):
            name = it.get("name", "")
            hist = it.get("history", []) or []
            uses = sum(int(h.get("uses", 0)) for h in hist)
            if not name:
                continue
            items.append({
                "platform": "Mastodon", "region": "global", "sub_region": "world",
                "rank": i, "title": name, "url": it.get("url", ""),
                "heat": uses, "category": None,
            })
    except Exception as e:
        items.append({"_error": f"mastodon:{e}"})
    return items
