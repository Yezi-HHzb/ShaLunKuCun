import requests
import json
import os

# 从环境变量读取飞书凭证
APP_ID = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]
APP_TOKEN = os.environ["FEISHU_APP_TOKEN"]
TABLE_ID = os.environ["FEISHU_TABLE_ID"]

def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    resp = requests.post(url, json=payload)
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取token失败: {data}")
    return data["tenant_access_token"]

def fetch_all_records(token):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/search"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    all_records = []
    page_token = None
    while True:
        payload = {"page_size": 500}
        if page_token:
            payload["page_token"] = page_token
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"获取记录失败: {data}")
        items = data.get("data", {}).get("items", [])
        all_records.extend(items)
        page_token = data.get("data", {}).get("page_token")
        if not page_token or len(items) < 500:
            break
    return all_records

def parse_records(records):
    result = []
    for rec in records:
        fields = rec.get("fields", {})
        # 获取“品号”字段的原始值
        part_no_raw = fields.get("品号", "")
        stock_raw = fields.get("库存", "")

        # 辅助函数：提取实际值
        def extract_value(raw):
            # 如果值是列表（多选或附件等），取第一个元素
            if isinstance(raw, list):
                raw = raw[0] if raw else ""
            # 如果值是字典，尝试提取 text 或 number 字段
            if isinstance(raw, dict):
                if "text" in raw:
                    return str(raw["text"]).strip()
                elif "number" in raw:
                    return str(raw["number"]).strip()
                elif "value" in raw:
                    return str(raw["value"]).strip()
                else:
                    # 如果都不存在，返回空字符串
                    return ""
            else:
                # 已经是字符串或数字
                return str(raw).strip() if raw is not None else ""

        part_no = extract_value(part_no_raw)
        stock = extract_value(stock_raw)

        if part_no:  # 只添加品号非空的记录
            result.append({"partNo": part_no, "stock": stock})
    return result

def main():
    token = get_tenant_access_token()
    records = fetch_all_records(token)
    data = parse_records(records)
    # 写入 data.json 到仓库根目录
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"成功同步 {len(data)} 条记录")

if __name__ == "__main__":
    main()
