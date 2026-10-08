import json
import requests
import sys
import os

# ====================== 配置 ======================
API_URL = "https://skills.sdicsc.com.cn/skill/api/v1/calc/query"
ENV_KEY = "GT_CROWDING_DEGREE_API_KEY"  # API Key环境变量名
INDUSTRY_FILE = "industry_info.json"
# ======================================================

def API_KEY() -> str:
    """从环境变量获取API Key"""
    key = os.getenv(ENV_KEY)
    if not key:
        raise ValueError(f"未配置API Key，请设置环境变量 {ENV_KEY}")
    return key

def load_industry_map():
    """加载行业映射表"""
    with open(INDUSTRY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    industry_map = {}
    for item in data.get("industry_info", []):
        code = item["S_INFO_WINDCODE"]
        name = item["S_INFO_NAME"]
        industry_map[code] = name
    return industry_map

def search_codes(keyword, industry_map):
    """模糊搜索匹配行业"""
    keyword_lower = keyword.lower()
    names = []
    codes = []
    for code, name in industry_map.items():
        if keyword_lower in name.lower():
            names.append(name)
            codes.append(code)
    return names, codes

def _headers() -> dict:
    api_key = os.getenv(ENV_KEY, "")
    return {
        "X-API-Key": api_key if api_key else "test-api-key",
        "Content-Type": "application/json"
    }

def get_crowding_data(codes):
    """请求拥挤度数据接口"""
    code_str = ",".join(codes)
    params = {"code": code_str}

    try:
        resp = requests.get(API_URL, params=params, headers=_headers(), timeout=10)
        
        # 检查HTTP状态码，处理鉴权失败
        if resp.status_code == 401:
            return {"code": 401, "msg": "未携带API Key，请先配置有效的API Key", "data": {}}
        elif resp.status_code == 403:
            return {"code": 403, "msg": "API Key无效，请检查配置或重新获取有效的API Key", "data": {}}
        elif resp.status_code != 200:
            return {"code": resp.status_code, "msg": f"请求失败，HTTP状态码: {resp.status_code}", "data": {}}
        
        return resp.json()
    except requests.exceptions.Timeout:
        return {"code": -1, "msg": "请求超时，请重试", "data": {}}
    except Exception as e:
        return {"code": -1, "msg": str(e), "data": {}}

def main(keyword):
    # 1. 加载行业映射
    industry_map = load_industry_map()

    # 2. 搜索匹配行业
    names, codes = search_codes(keyword, industry_map)
    if not codes:
        result = {
            "code": 404,
            "msg": f"未找到匹配行业: {keyword}",
            "data": []
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 3. 请求接口
    api_result = get_crowding_data(codes)

    # 检查API返回的错误码
    if api_result.get("code") in [401, 403]:
        print(json.dumps(api_result, ensure_ascii=False, indent=2))
        return

    # 4. 组装最终JSON
    final_data = []
    for code, name in zip(codes, names):
        final_data.append({
            "code": code,
            "name": name,
            "crowding_data": api_result.get("data", {}).get(code)
        })

    output = {
        "code": api_result.get("code", 200),
        "msg": f"找到 {len(final_data)} 个匹配行业",
        "data": final_data
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"code": 400, "msg": "缺少行业关键词"}, ensure_ascii=False))
        sys.exit(1)
    keyword = sys.argv[1]
    main(keyword)
