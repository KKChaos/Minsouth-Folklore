"""
从 Notion 数据库拉取闽南民俗知识库数据，生成 data.json
用法：python fetch_notion.py
需要环境变量：NOTION_TOKEN
"""

import os
import json
import urllib.request
import urllib.error

DATABASE_ID = "3681313e-55f3-80ed-8cad-000b48302f64"
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

if __name__ == "__main__":
    print("正在从 Notion 拉取数据…")
    entries = fetch_all()
    print(f"共获取 {len(entries)} 条")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print("已写入 data.json")
