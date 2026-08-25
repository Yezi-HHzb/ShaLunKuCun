import requests
import json
import os

# 飞书应用凭证
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

def extract_value(raw):
    """从飞书返回的字段值中提取纯文本或数字"""
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    if isinstance(raw, dict):
        if "text" in raw:
            return str(raw["text"]).strip()
        elif "number" in raw:
            return str(raw["number"]).strip()
        elif "value" in raw:
            return str(raw["value"]).strip()
        else:
            return ""
    else:
        return str(raw).strip() if raw is not None else ""

def parse_records(records):
    result = []
    for rec in records:
        fields = rec.get("fields", {})
        # 提取所有需要的字段
        part_no = extract_value(fields.get("厂料号", ""))
        # 兼容旧字段“品号”
        if not part_no:
            part_no = extract_value(fields.get("品号", ""))

        spec = extract_value(fields.get("规格型号", ""))
        manufacturer = extract_value(fields.get("厂家", ""))
        stock = extract_value(fields.get("库存", ""))
        linked_stock = extract_value(fields.get("联库", ""))
        total_stock = extract_value(fields.get("总库", ""))
        backup_stock = extract_value(fields.get("备货", ""))
        process = extract_value(fields.get("工序", ""))  # 新增工序字段

        if part_no:
            result.append({
                "partNo": part_no,
                "spec": spec,
                "manufacturer": manufacturer,
                "stock": stock,
                "linkedStock": linked_stock,
                "totalStock": total_stock,
                "backupStock": backup_stock,
                "process": process  # 新增
            })
    return result

def main():
    token = get_tenant_access_token()
    records = fetch_all_records(token)
    data = parse_records(records)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"成功同步 {len(data)} 条记录")

if __name__ == "__main__":
    main()
