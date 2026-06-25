"""
从 Notion 数据库拉取闽南民俗知识库数据，生成 data.json
用法：python fetch_notion.py
需要环境变量：NOTION_TOKEN
"""

import os
import json
import urllib.request
import urllib.error

DATABASE_ID = "3681313e-55f3-80e8-948b-d3b4b9c375ee"
NOTION_VERSION = "2022-06-28"

def notion_request(path, payload=None):
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("未设置环境变量 NOTION_TOKEN")

    url = f"https://api.notion.com/v1/{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def get_text(prop):
    """提取 rich_text 或 title 字段的纯文本"""
    if not prop:
        return ""
    items = prop.get("rich_text") or prop.get("title") or []
    return "".join(t.get("plain_text", "") for t in items)

def get_select(prop):
    if not prop:
        return ""
    sel = prop.get("select")
    return sel["name"] if sel else ""

def get_multi_select(prop):
    if not prop:
        return []
    return [s["name"] for s in prop.get("multi_select", [])]

def convert_entry(page):
    props = page.get("properties", {})
    url = page.get("url", "")

    return {
        "_title": get_text(props.get("条目名称")),
        "_url": url,
        "url": url,
        "条目名称": get_text(props.get("条目名称")),
        "白话字／拼音": get_text(props.get("白话字／拼音")),
        "大类": get_select(props.get("大类")),
        "子类": get_text(props.get("子类")),
        "地域层级": get_select(props.get("地域层级")),
        "适用地区": get_multi_select(props.get("适用地区")),
        "完成状态": get_select(props.get("完成状态")),
        "可信度": get_select(props.get("可信度")),
        "资料来源": get_text(props.get("资料来源")),
        "时间／时节": get_text(props.get("时间／时节")),
        "简单介绍": get_text(props.get("简单介绍")),
        "所需物品": get_text(props.get("所需物品")),
        "操作步骤": get_text(props.get("操作步骤")),
        "禁忌与避讳": get_text(props.get("禁忌与避讳")),
        "背后故事": get_text(props.get("背后故事")),
        "地域差异": get_text(props.get("地域差异")),
    }

def fetch_all():
    entries = []
    payload = {"page_size": 100}

    while True:
        result = notion_request(f"databases/{DATABASE_ID}/query", payload)
        for page in result.get("results", []):
            entry = convert_entry(page)
            if entry["条目名称"]:  # 跳过空标题
                entries.append(entry)

        if not result.get("has_more"):
            break
        payload["start_cursor"] = result["next_cursor"]

    return entries



# ── 排序配置 ──────────────────────────────────────────────
# 每个大类内条目的期望顺序（条目名称）。
# 不在列表中的新条目会追加到该大类末尾。
CATEGORY_ORDER = [
    "👶 人生礼仪",
    "🏠 宗族与日常礼节",
    "🍜 饮食民俗",
    "🌏 侨乡与海外传播",
    "🏡 传统建筑与工艺",
    "🎭 戏曲与口传文艺",
    "🙏 民间信仰",
    "🎉 岁时节庆",
]

ITEM_ORDER = {
    "👶 人生礼仪": [
        "做三朝", "做满月", "收涎（牙关饼）", "做四月日", "做度晬",
        "开笔礼（拜文昌）", "做十六岁", "订婚礼俗（送定）",
        "闽南婚礼", "归宁（新婚回门）", "做对年（周年祭）", "闽南丧葬",
    ],
    "🏠 宗族与日常礼节": [
        "开口吉（开嘴吉）", "正月初一诸禁忌", "初二回娘家",
        "闽南奉茶礼节", "闽南语言禁忌", "公妈厅祭祖",
        "宗祠文化", "族谱修撰", "入厝（乔迁之喜）",
        "做生日（生辰礼俗）", "分家习俗", "闽南称谓体系",
    ],
    "🍜 饮食民俗": [
        "润饼", "肉粽（闽南粽子）", "姜母鸭",
        "面线（寿面）", "土笋冻", "沙茶面", "海蛎煎",
        "碗糕", "满煎糕", "扁食（闽南馄饨）",
        "发糕（huat-kué）", "菜头粿（萝卜糕／煎馃）", "麻粩（炸枣）", "闽南咸粥",
    ],
    "🌏 侨乡与海外传播": [
        "过番（下南洋）", "侨批", "落叶归根文化", "闽南会馆（宗亲会）", "峇峇娘惹文化",
    ],
    "🏡 传统建筑与工艺": [
        "红砖厝", "泉州花灯", "德化瓷器", "惠安石雕",
        "漆线雕", "闽南木雕", "闽南刺绣（抽纱）", "闽南传统造船",
    ],
    "🎭 戏曲与口传文艺": [
        "南音", "梨园戏", "歌仔戏", "布袋戏（掌中戏）",
        "高甲戏", "提线木偶戏", "答嘴鼓", "闽南童谣与谚语", "讲古（闽南说书）",
    ],
    "🙏 民间信仰": [
        "清水祖师信仰", "临水夫人陈靖姑信仰", "三官大帝信仰",
        "妈祖信俗（土地公信仰）", "土地公（福德正神）信仰", "开漳圣王信仰（陈元光）",
        "玄天上帝（上帝公）信仰", "保生大帝信仰", "注生娘娘信仰", "妈祖信俗",
        "城隍信仰", "关圣帝君信仰", "法主公（张公圣君）信仰",
        "齐天大圣（孙悟空）信仰", "广泽尊王信仰", "田都元帅信仰",
        "太子爷（哪吒三太子）信仰", "石敢当信仰", "门神信仰",
        "妈祖信俗（送王船）", "妈祖信俗（王爷千岁信仰）", "王爷千岁信仰",
    ],
    "🎉 岁时节庆": [
        "出行迎财神（行好脚步）", "初三忌门（赤狗日）", "初四接神",
        "初五隔开（开市大吉）", "拜天公",
        "元宵听香", "元宵乞龟", "元宵看花灯",
        "清明培墓",
        "端午扒龙船", "嗦啰嗹", "端午午时水",
        "七夕拜七娘妈", "中元普渡",
        "中秋博饼", "八月十五拜月",
        "冬至搓圆",
        "尾牙", "送神（谢灶）", "掸尘（送神后大扫除）", "贴春联", "围炉",
    ],
}

def sort_entries(entries):
    """按 CATEGORY_ORDER 和 ITEM_ORDER 排序，新条目追加到该大类末尾。"""
    buckets = {cat: [] for cat in CATEGORY_ORDER}
    others = []
    for e in entries:
        cat = e.get("大类", "")
        if cat in buckets:
            buckets[cat].append(e)
        else:
            others.append(e)

    result = []
    for cat in CATEGORY_ORDER:
        order = ITEM_ORDER.get(cat, [])
        rank = {name: i for i, name in enumerate(order)}
        sorted_items = sorted(
            buckets[cat],
            key=lambda e, r=rank, n=len(order): r.get(e.get("条目名称", ""), n)
        )
        result.extend(sorted_items)
    result.extend(others)
    return result
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("正在从 Notion 拉取数据…")
    entries = fetch_all()
    print(f"共获取 {len(entries)} 条")

    entries = sort_entries(entries)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print("已写入 data.json")
