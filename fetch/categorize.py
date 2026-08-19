# -*- coding: utf-8 -*-
"""把热词归类到行业。默认关键词规则法（免费、可靠）；未命中按区域兜底。"""

from config import CATEGORY_KEYWORDS


def categorize(title, region="cn"):
    if not title:
        return "社会" if region == "cn" else "国际"
    t = title.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in t:
                return cat
    # 未命中：国内归"社会"，全球归"国际"
    return "社会" if region == "cn" else "国际"
