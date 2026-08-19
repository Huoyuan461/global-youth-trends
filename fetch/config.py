# -*- coding: utf-8 -*-
"""配置文件：数据源端点、请求头、分类词表、热度解析工具。

所有端点均在 2026-08-18 实测可达。国内源免费为主，抖音走聚合兜底；
全球源免费为主（Google Trends / Hacker News / GDELT / Google News / Mastodon）。
"""

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# 国内数据源端点
CN_SOURCES = {
    "baidu": "https://top.baidu.com/api/board?platform=wise&tab=realtime",
    "bilibili": "https://api.bilibili.com/x/web-interface/popular?ps=20",
    "zhihu": "https://www.zhihu.com/api/v3/feed/topstory/hot-list-web",
    "weibo": "https://weibo.com/ajax/side/hotSearch",
    "juhe": "https://apis.juhe.cn/fapigx/networkhot/query",  # 需 JUHE_KEY
}

# 全球数据源端点
GLOBAL_SOURCES = {
    "hn": "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30",
    "trends": "https://trends.google.com/trending/rss?geo={geo}",
    "gdelt": "https://api.gdeltproject.org/api/v2/doc/doc",
    "gnews": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "mastodon": "https://mastodon.social/api/v1/trends",
}

# 默认抓取的地区（Google Trends）
TRENDS_GEOS = ["US", "GB", "JP"]

# 通用请求头（知乎/微博需要 UA + Referer，否则 403/401）
HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://www.zhihu.com/",
    "Accept": "application/json, text/plain, */*",
}

# 行业分类关键词（中英混合，小写匹配）
CATEGORY_KEYWORDS = {
    "科技": ["ai", "tech", "software", "startup", "app", "芯片", "大模型", "人工智能",
            "手机", "特斯拉", "发布", "算法", "量子", "机器人", "自动驾驶", "华为", "苹果", "显卡"],
    "娱乐": ["celebrity", "movie", "music", "明星", "电影", "综艺", "演唱会", "票房",
            "塌房", "电视剧", "网红", "直播", " idol", "歌手", "导演"],
    "游戏": ["game", "steam", "ps5", "xbox", "switch", "原神", "王者", "电竞", "主播",
            "游戏", "英雄联盟", "手游", "二次元"],
    "财经": ["market", "stock", "crypto", "股", "基金", "楼市", "央行", "通胀", "上市",
            "经济", "理财", "黄金", "比特币", "a股", "汇率"],
    "教育": ["college", "exam", "高考", "考研", "大学", "双减", "留学", "学校",
            "教师", "中考", "保研", "学历"],
    "情感": ["dating", "relationship", "恋爱", "婚姻", "分手", "渣男", "脱单",
            "相亲", "彩礼", "异地恋"],
    "体育": ["nba", "world cup", "olympic", "奥运", "夺冠", "转会", "足球", "篮球",
            "世界杯", "球赛", "联赛"],
    "国际": ["ukraine", "election", "美国", "乌克兰", "外交部", "联合国", "日本",
            "韩国", "欧洲", "总统", "战争", "俄", "白宫"],
    "健康": ["covid", "health", "疫情", "医院", "医保", "疾病", "养生", "减肥",
            "病毒", "疫苗", "体检"],
    "时政": ["policy", "government", "国务院", "政策", "主席", "总理", "人大",
            "改革", "法规", "部长", "中央"],
}


def parse_heat(raw):
    """把各种热度文本解析成整数。支持 '200+'、'1,234'、'1234 万热度'、'2.3亿'。"""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        try:
            return int(raw)
        except (ValueError, OverflowError):
            return None
    s = str(raw).replace(",", "").strip()
    if not s:
        return None
    import re
    m = re.search(r"([\d.]+)\s*(亿|万)?", s)
    if not m:
        return None
    try:
        num = float(m.group(1))
    except ValueError:
        return None
    unit = m.group(2)
    if unit == "亿":
        num *= 1e8
    elif unit == "万":
        num *= 1e4
    return int(num)
