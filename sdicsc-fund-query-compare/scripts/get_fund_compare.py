"""
基金对比分析脚本。

功能：
- 循环调用get_fund_data.py获取多只基金数据
- 生成JSON数据文件（包含基金数据和走势数据）
- 智能体根据JSON数据直接输出Markdown分析报告

使用方法：
    python3 get_fund_compare.py --funds "000001,000002"
"""

import argparse
import asyncio
import json
import sys
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))
from get_fund_data import Config, get_fund_data, FieldMapper


def _get_default_output_dir() -> Path:
    """返回默认输出目录路径（当前skill根目录下的.output子目录）。"""
    script_dir = Path(__file__).resolve().parent
    # 向上一级: scripts -> sdicsc-fund-query-compare (skill根目录)
    skill_dir = script_dir.parent
    return skill_dir / ".output"


async def fetch_funds(fund_codes: List[str]) -> Tuple[List[Dict[str, Any]], List[Any]]:
    """并行获取多只基金数据。返回 (基金数据列表, 走势原始数据列表)。"""
    # 前置校验API Key，避免9个并行请求因Key缺失同时失败
    try:
        Config.API_KEY()
    except Exception as e:
        error_funds = [{"code": c, "error": f"API Key校验失败: {str(e)}"} for c in fund_codes]
        return error_funds, [None] * len(fund_codes)

    tasks = [get_fund_data(code) for code in fund_codes]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    funds = []
    trend_raw_list = []  # 暂时屏蔽走势数据，返回空列表
    
    for i, result in enumerate(results):
        if isinstance(result, BaseException):
            funds.append({"code": fund_codes[i], "error": str(result)})
            trend_raw_list.append(None)
        else:
            # result是dict类型
            # 移除trend字段，避免在fund_compare.json中重复保存
            result.pop("trend", None)
            funds.append(result)
            # 暂时屏蔽走势数据生成，不提取trend数据
            # trend_raw_list.append(result.get("trend"))
            trend_raw_list.append(None)
    
    return funds, trend_raw_list


def _is_valid_fund(f: Dict[str, Any]) -> bool:
    """判断基金数据是否有效（有核心字段即可，部分子接口error不影响整体有效性）。"""
    # 有基金名称即视为有效（核心数据已返回，即使部分子接口超时）
    return bool(f.get("name"))


def generate_summary(funds: List[Dict[str, Any]]) -> str:
    valid_funds = [f for f in funds if _is_valid_fund(f)]
    if not valid_funds:
        return "未能获取到有效基金数据"
    names = [f.get("name", "") for f in valid_funds]
    return f"已对比 {len(valid_funds)} 只基金: {', '.join(names)}"


class OutputGenerator:
    def __init__(self, output_dir: Optional[Path] = None):
        self._base_dir = output_dir or _get_default_output_dir()
        self.unique_id = uuid.uuid4().hex[:8]
        self.output_dir = self._base_dir / self.unique_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_trend_json(self, trend_original_list: List[Any], funds: List[Dict[str, Any]]) -> Path:
        """
        生成走势图JSON数据文件，沪深300数据作为特殊基金项合并到funds数组中。
        
        注意：该功能暂时屏蔽，减少不必要的文件输出。
        如需恢复，取消get_fund_compare函数中的注释即可。
        """
        valid_funds = [f for f in funds if _is_valid_fund(f)]
        fund_names = {f.get("code"): f.get("name", f.get("code")) for f in valid_funds}

        trend_data = {"funds": []}
        
        # 添加各基金的走势数据（不包含hs300_return）
        for i, trend in enumerate(trend_original_list):
            if trend is None:
                continue
            code = funds[i].get("code", "") if i < len(funds) else ""
            
            # 提取基金收益率数据（去掉hs300_return）
            # trend 是一个列表 [{"date": "...", "fund_return": "...", "hs300_return": "..."}, ...]
            fund_trend_data = []
            if isinstance(trend, list):
                for item in trend:
                    if "date" in item and "fund_return" in item:
                        fund_trend_data.append({
                            "date": item["date"],
                            "return": item["fund_return"]
                        })
            
            trend_data["funds"].append({
                "code": code,
                "name": fund_names.get(code, ""),
                "trend": fund_trend_data
            })
        
        # 提取沪深300数据（只取第一只基金的，避免重复），作为特殊基金项添加到funds数组末尾
        if trend_original_list and trend_original_list[0] is not None:
            first_trend = trend_original_list[0]
            if isinstance(first_trend, list):
                hs300_data = []
                for item in first_trend:
                    if "date" in item and "hs300_return" in item:
                        hs300_data.append({
                            "date": item["date"],
                            "return": item["hs300_return"]
                        })
                # 将沪深300作为特殊基金项添加到funds数组末尾，确保trend结构一致
                trend_data["funds"].append({
                    "code": "hs300",
                    "name": "沪深300",
                    "trend": hs300_data
                })

        json_path = self.output_dir / f"fund_trend_{self.unique_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(trend_data, f, ensure_ascii=False, indent=2)
        return json_path


async def get_fund_compare(fund_codes: str) -> Dict[str, Any]:
    """获取基金对比数据，生成JSON文件。"""
    codes = [c.strip() for c in fund_codes.split(",") if c.strip()]
    if len(codes) < 1:
        raise ValueError("至少需要1只基金")
    if len(codes) > 5:
        raise ValueError("最多支持5只基金，请减少基金数量后重试")

    funds, trend_raw_list = await fetch_funds(codes)
    summary = generate_summary(funds)

    generator = OutputGenerator()
    json_path = generator.output_dir / f"fund_compare_{generator.unique_id}.json"
    # 暂时屏蔽走势数据生成，减少不必要的文件输出
    # trend_json_path = generator.generate_trend_json(trend_raw_list, funds)

    # 使用OrderedDict确保字段顺序：概要信息在前，详细数据在后
    result: Dict[str, Any] = OrderedDict([
        ("timestamp", datetime.now(timezone.utc).isoformat()),
        ("summary", summary),
        ("fund_count", len(codes)),
        ("fund_codes", codes),
        ("output_files", {
            "json": str(json_path),
            # "trend_json": str(trend_json_path),  # 暂时屏蔽
        }),
        ("meta", {
            "field_mapping": FieldMapper.get_field_mapping(),
            "data_source": "国投证券",
        }),
        ("funds", funds),  # 详细数据放最后
    ])
    
    # 写入主JSON文件
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def main():
    parser = argparse.ArgumentParser(description="基金对比分析")
    parser.add_argument("--funds", required=True, help="基金代码，逗号分隔")
    args = parser.parse_args()

    result = asyncio.run(get_fund_compare(args.funds))
    
    # stdout只输出概要信息，避免输出过长导致截断
    # 智能体应从output_files.json路径读取完整数据
    summary_output = OrderedDict([
        ("timestamp", result["timestamp"]),
        ("summary", result["summary"]),
        ("fund_count", result["fund_count"]),
        ("fund_codes", result["fund_codes"]),
        ("output_files", result["output_files"]),
        ("meta", result["meta"]),
    ])
    print(json.dumps(summary_output, ensure_ascii=False))


if __name__ == "__main__":
    main()