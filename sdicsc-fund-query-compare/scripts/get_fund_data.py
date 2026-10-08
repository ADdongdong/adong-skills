"""
单只基金数据查询脚本。

功能：
- 单只基金多维度数据获取
- 返回结果的中英文映射、枚举转换
- JSON格式输出，可直接被skill调用

使用方法：
    python3 get_fund_data.py --fund 005827 --output ../.output/result.json
"""

import argparse
import asyncio
import json
import re
import ssl
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

def is_business_error(data) -> bool:
    """判断是否为业务异常
    只有当 code 为 "000", "401", "403", "500" 或code不为0返回 True（异常）
    其他情况（包括 list 类型、正常数据）都返回 False（正常）
    """
    if not isinstance(data, dict):
        return False
    code = data.get("code")
    if code is not None and str(code) in ("000", "401", "403", "404", "500","503","429"):
        return True
    # code不为0也视为异常
    try:
        if code is not None and int(code) != 0: 
            return True
    except (ValueError, TypeError):
        pass
    return False

import httpx


# ==================== 配置 ====================

class Config:
    """全局配置"""

    # API配置
    BASE_URL = "https://skills.sdicsc.com.cn/skill"  # API基础地址

    @staticmethod
    def _load_api_key_from_memory() -> Optional[str]:
        """从memory.md自动加载API Key"""
        script_dir = Path(__file__).resolve().parent
        skill_dir = script_dir.parent
        memory_path = skill_dir / "memory.md"

        if memory_path.exists():
            try:
                content = memory_path.read_text(encoding="utf-8")
                match = re.search(r'API Key:\s*(\S+)', content)
                if match:
                    return match.group(1)
            except Exception:
                pass
        return None

    @staticmethod
    def API_KEY() -> str:
        """获取API Key，从memory.md加载"""
        key = Config._load_api_key_from_memory()
        if not key:
            raise Exception("API Key未配置.")
        return key

    # 接口路由 (根据API.md)
    ROUTES = {
        "fund_detail": "/msps-fstore/ajs/fund/new/v2/queryFundDetails.do",
        "fund_perf": "/msps-fstore/ajs/fund/new/queryPerformance.do",
        "fund_manager": "/msps-fstore/ajs/fund/new/v2/queryFundManagerInfo.do",
        "fund_manager_detail": "/msps-fstore/choiceness/queryFundManagerDetails.do",
        "fund_rate": "/msps-fstore/ajs/fund/new/v2/queryFundTransRule.do",
        "fund_holding": "/msps-fstore/ajs/fund/new/queryAssetAllocation.do",
        "fund_risk": "/msps-fstore/ajs/fund/new/queryFundDiagnoseAnalyse.do",
        "fund_trend": "/msps-fstore/ajs/fund/new/v1/queryFundTrend.do",
        "fund_basic_info": "/msps-fstore/ajs/fund/new/queryFundBasicInfo.do",
        "fund_simple_info": "/msps-fstore/ajs/fund/new/queryFundSimpleInfo.do",
    }

    # SSL配置
    SSL_CONTEXT = ssl.create_default_context()


# ==================== 枚举映射 ====================

class EnumMapper:
    """枚举值中英文映射"""

    # 风险等级映射 (API: riskGrade 1-5)
    RISK_LEVEL_MAP = {
        "0": "低风险",
        "1": "中低风险",
        "2": "中等风险",
        "3": "中高风险",
        "4": "高风险",
    }

    # 基金规模单位映射
    SCALE_UNIT_MAP = {
        '1': "亿",
        '2': "万"
    }

    # 评级映射
    RATING_MAP = {
        "5": "5星",
        "4": "4星",
        "3": "3星",
        "2": "2星",
        "1": "1星",
    }

    # 基金状态映射
    FUND_STATUS_MAP = {
        "0": "正常交易",
        "1": "发行",
        "2": "发行成功",
        "3": "发行失败",
        "4": "基金停止交易",
        "5": "停止申购",
        "6": "停止赎回",
        "7": "权益登记",
        "8": "红利发放",
        "9": "基金封闭",
        "a": "基金终止",
    }

    # 是否管理中映射 (is_position字段: 1=管理中, 0=否)
    IS_POSITION_MAP = {
        "1": "是",
        "0": "否",
    }

    @classmethod
    def map_rating(cls, value: str) -> str:
        """映射评级"""
        return cls.RATING_MAP.get(value, value)

    @classmethod
    def map_fund_status(cls, value: str) -> str:
        """映射基金状态"""
        return cls.FUND_STATUS_MAP.get(value, value)

    @classmethod
    def map_is_position(cls, value: str) -> str:
        """映射是否管理中"""
        return cls.IS_POSITION_MAP.get(value, value)


# ==================== 字段映射 ====================

class FieldMapper:
    """字段中英文映射"""

    # 字段名称映射 - 用于meta.field_mapping
    FIELD_NAME_MAP = {
        # 基本信息
        "code": "基金代码",
        "name": "基金简称",
        "type": "基金类型",
        "risk_level": "风险等级",
        "net_value": "单位净值",
        "net_date": "净值日期",
        "accumulated_net_value": "累计净值",
        "establish_date": "成立日期",
        "manager": "基金管理人",
        "custodian": "基金托管人",

        # 基本信息-扩展字段
        "tag_names": "基金标签",
        "fund_star": "基金星级",
        "yield_day": "日涨跌幅",
        "theme_labels": "主题标签",
        "min_buy": "最低购买金额",
        "fund_status": "基金状态",
        "is_auto_invest": "是否支持定投",

        # 费率信息
        "fees": "费率信息",
        "management": "管理费率",
        "custodian_fee": "托管费率",
        "subscription": "申购费率",
        "redemption": "赎回费率",

        # 费率信息-扩展字段
        "fee_type_name": "收费方式",
        "sale_service_rate": "销售服务费率",
        "apply_buy_rate_list": "申购费率阶梯",
        "redeem_rate_list": "赎回费率阶梯",

        # 规模信息
        "scale": "基金规模",

        # 持仓信息
        "holdings": "持仓信息",
        "asset_allocation": "资产配置",

        # 持仓信息-扩展字段
        "stock_list": "股票持仓列表",
        "stk_name": "股票名称",
        "stk_code": "股票代码",
        "stk_chg": "股票最新涨跌幅",
        "stk_price": "股票最新价",
        "stk_ratio": "股票占净值比例",

        "bond_list": "债券持仓列表",
        "bond_name": "债券名称",
        "bond_code": "债券代码",
        "bond_ratio": "债券占净值比例",

        "fund_list": "基金持仓列表",
        "fund_name": "基金名称",
        "fund_code": "基金代码",
        "fund_ratio": "基金占净值比例",

        "industry_allocation": "行业配置",
        "industry_code": "行业代码",
        "industry_name": "行业名称",
        "industry_ratio": "行业占净值比例",

        # 业绩相关
        "performance": "业绩表现",
        "return_1w": "近1周收益率",
        "return_1m": "近1月收益率",
        "return_3m": "近3月收益率",
        "return_6m": "近6月收益率",
        "return_1y": "近1年收益率",
        "return_3y": "近3年收益率",
        "return_5y": "近5年收益率",
        "return_ytd": "今年来收益率",
        "rank_1w": "近1周排名",
        "rank_1m": "近1月排名",
        "rank_3m": "近3月排名",
        "rank_6m": "近6月排名",
        "rank_1y": "近1年排名",
        "rank_3y": "近3年排名",
        "rank_5y": "近5年排名",
        "hs300_rate_1m": "近1月沪深300收益率",
        "hs300_rate_3m": "近3月沪深300收益率",
        "hs300_rate_6m": "近6月沪深300收益率",
        "hs300_rate_1y": "近1年沪深300收益率",
        "hs300_rate_3y": "近3年沪深300收益率",

        # 风险指标
        "risk": "风险指标",
        "max_drawdown": "近一年最大回撤",
        "volatility": "波动率",
        "sortino_ratio": "索提诺比率",
        "information_ratio": "信息比率",
        "calmar_ratio": "卡玛比率",

        # 风险指标-扩展字段
        "prod_rating_detail": "产品评级详情",
        "anti_risk_capability": "抗风险能力",
        "profit_ability": "盈利能力",
        "composite_rating": "综合评级",
        "excess_earning_power": "超额收益能力",
        "reference_tracking_capability": "基准跟踪能力",
        "stock_selection_ability": "选股能力",
        "performance_stability": "业绩稳定性",

        # 风险指标-排名字段
        "volatility_rank": "波动率排名",
        "information_ratio_rank": "信息比率排名",
        "max_drawdown_rank": "近一年最大回撤排名",

        # 基金经理
        "fund_managers": "基金经理",
        "manager_name": "基金经理姓名",
        "manager_code": "基金经理代码",
        "start_date": "任职日期",
        "end_date": "离任日期",
        "manager_scale": "管理规模",
        "annual_return": "本基金任职期总回报",
        "company": "基金公司",
        "management_scale": "管理规模(亿)",
        "service_year": "任职年限",
        "annual_yield": "从业以来年化收益",
        "synopsis": "基金经理简介",

        # 基金经理-扩展字段
        "manager_tag_names": "经理标签",
        "manager_hold_days": "任职天数",
        "manage_fund_list": "管理基金列表",
        "manage_fund_name": "管理基金名称",
        "is_position": "是否管理中",

        # 基金经理对比（用于MD报告）
        "manager_names": "基金经理",
        "yield_since": "任职年化收益",
        "yield_hs300": "同期沪深300收益",
        "manager_companies": "基金公司",
        "manager_scales": "管理规模(亿)",
        "manager_service_years": "任职年限",

        # 基金经理在任基金列表
        "mf_fund_name": "在任基金名称",
        "mf_fund_code": "在任基金代码",
        "mf_hold_start_date": "在任基金管理开始时间",
        "mf_hold_end_date": "在任管理结束时间",
        "mf_hold_days": "在任基金管理天数",
        "mf_yield_since": "在任基金任期总回报",
        "mf_yield_hs300": "在任基金同期沪深300收益",
        "mf_is_position": "在任基金管理状态",
        "mf_rank": "在任基金近一年排名",

        # 持仓对比（用于MD报告）
        "stock_ratio": "股票仓位",

        # 交易规则
        "trans_detail": "交易规则",
        "confirm_date": "确认日期",
        "sell_confirm_date": "赎回确认日期",
        "buy_date": "购买日期",
        "sell_date": "赎回日期",
        "earnings_date": "收益到账日期",

        # 走势数据
        "trend": "走势数据",
        "hs300_rate": "沪深300收益率",
        "return_rate": "基金收益率",

        # 其他
        "error": "错误信息",
        "timestamp": "数据时间",
    }

    @classmethod
    def get_field_mapping(cls) -> dict:
        """获取完整的字段映射字典"""
        return cls.FIELD_NAME_MAP.copy()

    @classmethod
    def map_field_name(cls, field: str) -> str:
        """映射字段名称"""
        return cls.FIELD_NAME_MAP.get(field, field)


# ==================== 数据模型 ====================

class FundData:
    """基金数据模型"""

    def __init__(self, code: str):
        self.code = code
        self.name = ""
        self.type = ""
        self.risk_level = ""
        self.net_value = ""
        self.net_date = ""
        self.accumulated_net_value = ""
        self.establish_date = ""
        self.manager = ""
        self.custodian = ""
        self.management_fee = ""
        self.custodian_fee = ""
        self.subscription_fee = ""
        self.redemption_fee = ""
        self.scale = ""
        self.holdings = []
        self.performance = {}
        self.risk = {}
        self.fund_managers = []
        self.error = ""
        # 交易规则详情
        self.trans_detail = {}
        # 风险评级详情
        self.prod_rating_detail = {}

        # 扩展字段 - 基金基本信息相关
        self.tag_names = ""  # 基金标签
        self.fund_star = ""  # 基金星级
        self.yield_day = ""  # 日涨跌幅
        self.theme_labels = ""  # 主题标签
        self.min_buy = ""  # 最低购买金额
        self.fund_status = ""  # 基金状态
        self.is_auto_invest = ""  # 是否支持定投

        # 费率相关扩展字段
        self.fee_type_name = ""  # 收费方式
        self.sale_service_rate = ""  # 销售服务费率

        # 走势图数据
        self.trend = []  # 走势数据
        # 各维度请求异常记录（结构化错误提示）
        self.fetch_errors = []

    def to_dict(self) -> dict:
        result = {}

        # 1. 基本信息
        result["code"] = self.code
        result["name"] = self.name
        result["type"] = self.type
        result["risk_level"] = self.risk_level
        result["net_value"] = self.net_value
        result["net_date"] = self.net_date
        result["accumulated_net_value"] = self.accumulated_net_value
        result["establish_date"] = self.establish_date
        result["manager"] = self.manager
        result["custodian"] = self.custodian
        if self.scale:
            result["scale"] = self.scale
        if self.tag_names:
            result["tag_names"] = self.tag_names
        if self.fund_star:
            result["fund_star"] = self.fund_star
        if self.yield_day:
            result["yield_day"] = self.yield_day
        if self.theme_labels:
            result["theme_labels"] = self.theme_labels
        if self.min_buy:
            result["min_buy"] = self.min_buy
        if self.fund_status:
            result["fund_status"] = self.fund_status
        if self.is_auto_invest:
            result["is_auto_invest"] = self.is_auto_invest
        if self.prod_rating_detail:
            result["prod_rating_detail"] = self.prod_rating_detail           

        # 2. 费率信息、交易规则
        fees = {}
        if self.management_fee:
            fees["management"] = self.management_fee
        if self.custodian_fee:
            fees["custodian_fee"] = self.custodian_fee
        if self.subscription_fee:
            fees["subscription"] = self.subscription_fee
        if self.redemption_fee:
            fees["redemption"] = self.redemption_fee
        if self.fee_type_name:
            fees["fee_type_name"] = self.fee_type_name
        if self.sale_service_rate:
            fees["sale_service_rate"] = self.sale_service_rate
        if fees:
            result["fees"] = fees

        if self.trans_detail:
            result["trans_detail"] = self.trans_detail

        # 3. 业绩表现
        if self.performance:
            result["performance"] = self.performance

        # 4. 风险指标
        if self.risk:
            result["risk"] = self.risk

        # 5. 持仓信息
        if self.holdings:
            result["holdings"] = self.holdings

        # 6. 基金经理
        if self.fund_managers:
            result["fund_managers"] = self.fund_managers

        # 7. 错误信息
        if self.error:
            result["error"] = self.error

        # 8. 各维度请求异常记录
        if self.fetch_errors:
            result["fetch_errors"] = self.fetch_errors




        # 12. 走势图
        if self.trend:
            result["trend"] = self.trend

        return result


# ==================== API客户端 ====================

class FundAPIClient:
    """基金数据API客户端"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0, verify=Config.SSL_CONTEXT)

    def _parse_json(self, resp: httpx.Response) -> dict:
        """解析 JSON 响应，处理异常格式"""
        try:
            return resp.json()
        except json.JSONDecodeError:
            # 尝试提取第一个 JSON 对象（非贪婪匹配）
            text = resp.text.strip()
            match = re.match(r'\{.*?\}', text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {"code": resp.status_code, "message": text}

    def _headers(self) -> dict:
        return {
            "X-API-Key": Config.API_KEY(),
            "Content-Type": "application/json"
        }

    def _params(self, **extra) -> dict:
        p = {"source": "fund_compare"}
        p.update(extra)
        return p

    async def get_fund_detail(self, code: str) -> Optional[dict]:
        """获取基金详情信息"""
        url = f"{self.base_url}{Config.ROUTES['fund_detail']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code, fundSource='1'),
                                          headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # API.md返回格式: data.data.fundDetail
            fund_detail = data.get("data", {}).get("fundDetail") or data.get("data", {}).get("newFundDetail")
            if fund_detail:
                return fund_detail
            else:
                return data  # 基金不存在时返回包含错误信息的完整响应
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_base_info(self, code: str) -> Optional[dict]:
        """获取基金基本信息"""
        url = f"{self.base_url}{Config.ROUTES['fund_basic_info']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code, fundSource='1'),
                                          headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # API.md返回格式: data.data.fundDetail
            return data.get("data", {}) if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_simple_info(self, code: str) -> Optional[dict]:
        """获取基金简介信息"""
        url = f"{self.base_url}{Config.ROUTES['fund_simple_info']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code), headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # API.md返回格式: data.data.fundDetail
            return data.get("data", {}) if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_performance(self, code: str) -> Optional[dict]:
        """获取基金业绩"""
        url = f"{self.base_url}{Config.ROUTES['fund_perf']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code, queryAll='N'),
                                          headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # API.md返回格式: data.data.dataList
            return data.get("data", {}).get("dataList") if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_manager(self, code: str) -> Optional[dict]:
        """获取基金经理信息"""
        url = f"{self.base_url}{Config.ROUTES['fund_manager']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code), headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # API.md返回格式: data.data.fundManagerList
            return data.get("data", {}).get("fundManagerList") if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_rate(self, code: str) -> Optional[dict]:
        """获取基金费率"""
        url = f"{self.base_url}{Config.ROUTES['fund_rate']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code, fundSource='1'),
                                          headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # API.md返回格式: 直接返回data.data下的费率相关字段
            return data.get("data") if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_holding(self, code: str, asset_type: str = "1") -> Optional[dict]:
        """获取基金持仓（资产配置或行业分布）

        Args:
            code: 基金代码
            asset_type: 资产类型，'1'=资产配置，'2'=行业分布
        """
        url = f"{self.base_url}{Config.ROUTES['fund_holding']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code, assetType=asset_type),
                                          headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # API.md返回格式: data.data包含assetTotal, assetAllocationList, stockList等
            return data.get("data") if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_industry(self, code: str) -> Optional[dict]:
        """获取基金行业分布"""
        return await self.get_fund_holding(code, asset_type="2")

    async def get_fund_risk(self, code: str) -> Optional[dict]:
        """获取完整风险数据（包括产品评级详情）"""
        url = f"{self.base_url}{Config.ROUTES['fund_risk']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code), headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # 返回完整的data对象，包含technologyList和prodRatingDetail
            return data.get("data") if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_trend(self, code: str) -> Optional[dict]:
        """获取基金业绩走势"""
        url = f"{self.base_url}{Config.ROUTES['fund_trend']}"
        try:
            resp = await self.client.post(url, params=self._params(fundCode=code, rankRule=12, isQueryTrd='N',
                                                                   isQueryCost='N'), headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # 返回完整的data对象，包含dataList, hs300Rate, returnRate等
            return data.get("data") if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def get_fund_manager_detail(self, manager_code: str) -> Optional[dict]:
        """获取基金经理详情"""
        url = f"{self.base_url}{Config.ROUTES['fund_manager_detail']}"
        try:
            resp = await self.client.post(url, params=self._params(fundManagerCode=manager_code),
                                          headers=self._headers())
            data = self._parse_json(resp)
            # 检查 HTTP 状态码，如果是错误状态则返回原始响应
            if resp.status_code >= 400:
                return data
            # API.md返回格式: data.data.dataList
            return data.get("data", {}) if data.get("data") else None
        except Exception as e:
            return {"code": "000", "message": f"服务暂不可用，请稍后再试 ({type(e).__name__})", "raw_response": resp.text if 'resp' in locals() else ""}

    async def close(self):
        await self.client.aclose()


# ==================== 数据解析器 ====================

class FundDataParser:
    """基金数据解析器 - 负责数据解析和映射转换"""

    @staticmethod
    def parse_detail(fund: FundData, data: dict):
        """解析基本信息 (API: /msps-fstore/ajs/fund/new/v2/queryFundDetails.do)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        # API返回字段映射
        fund.code = data.get("fundCode", "")
        fund.name = data.get("fundName", "")

        # 基金类型 (fundSortName: 混合型, 股票型等)
        fund.type = data.get("fundSortName", "")

        # 风险等级
        riskGrade = data.get("riskGrade", "")
        fund.risk_level = EnumMapper.RISK_LEVEL_MAP.get(riskGrade)

        # 净值信息
        fund.net_value = data.get("nvPer", "")  # 单位净值
        fund.accumulated_net_value = data.get("anvPer", "")  # 累计净值
        fund.net_date = data.get("endDate", "")  # 净值日期

        # 费率
        fund.management_fee = data.get("rate", "")

        # 扩展字段 - 直接存储为一级字段
        # 基金标签
        fund.tag_names = data.get("tagNames", "")

        # 基金星级
        fund_star = data.get("fundStar", "")
        fund.fund_star = EnumMapper.map_rating(fund_star)

        # 日涨跌幅
        fund.yield_day = data.get("yieldDay") + '%' if data.get("yieldDay") else None

        # 主题标签
        theme_label_list = data.get("themeLabelList", [])
        if theme_label_list:
            fund.theme_labels = ",".join(theme_label_list) if isinstance(theme_label_list, list) else theme_label_list

        if data.get("purchasingRules"):
            # 最低购买金额
            fund.min_buy = data.get("minBuy") + '份' if data.get("minBuy") else None
        else:
            # 最低购买金额
            fund.min_buy = data.get("minBuy") + '元' if data.get("minBuy") else None

        # 基金状态
        fund_status = data.get("fundStatus", "")
        fund.fund_status = EnumMapper.map_fund_status(fund_status)

        # 是否支持定投 (从isProto字段判断)
        is_proto = data.get("isProto", "")
        if is_proto == "0":
            fund.is_auto_invest = "支持"
        else:
            fund.is_auto_invest = "不支持"

    @staticmethod
    def parse_performance(fund: FundData, data: dict):
        """解析业绩数据 (API: /msps-fstore/ajs/fund/new/queryPerformance.do)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        # API返回格式: dataList数组，每个元素包含timeType, rate, rankingNum, totalNum
        # timeType: 近一月, 近三月, 近六月, 近一年, 近三年

        performance = {}

        # 时间类型映射
        time_type_map = {
            "近一月": "return_1m",
            "近三月": "return_3m",
            "近六月": "return_6m",
            "近一年": "return_1y",
            "近三年": "return_3y",
        }

        if isinstance(data, list):
            for item in data:
                time_type = item.get("timeType", "")
                output_key = time_type_map.get(time_type)
                if output_key:
                    # 收益率
                    rate = item.get("rate", "")
                    if rate:
                        performance[output_key] = f"{rate}%"

                    # 排名
                    ranking_num = item.get("rankingNum", "")
                    total_num = item.get("totalNum", "")
                    if ranking_num and total_num:
                        performance[f"rank_{output_key.split('_')[1]}"] = f"{ranking_num}/{total_num}"

                    # 沪深300收益率 (aveRate字段)
                    ave_rate = item.get("aveRate", "")
                    if ave_rate:
                        performance[f"hs300_rate_{output_key.split('_')[1]}"] = f"{ave_rate}%"

        fund.performance = performance

    @staticmethod
    def parse_manager(fund: FundData, data: dict):
        """解析基金经理数据 (API: /msps-fstore/ajs/fund/new/v2/queryFundManagerInfo.do)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        # API返回格式: fundManagerList数组，每个元素包含manageFundInfoDtos
        if isinstance(data, list) and data:
            managers = []
            for m in data:

                manager_info = {
                    "name": m.get("personName", ""),
                    "code": m.get("personCode", ""),
                    "start_date": m.get("postDate", ""),
                    "end_date": "",
                    "annual_return": m.get("yieldSinces") + '%' if m.get("yieldSinces") else None,
                }

                # 扩展字段
                tag_names = m.get("tagNames", "")
                if tag_names:
                    manager_info["manager_tag_names"] = tag_names

                yield_hs300 = m.get("yieldHS300")
                if yield_hs300:
                    manager_info["yield_hs300"] = yield_hs300 + '%'

                hold_days = m.get("holdDays", "")
                if hold_days:
                    manager_info["manager_hold_days"] = hold_days

                # 管理基金列表
                manage_fund_info = m.get("manageFundInfoDtos", [])
                if manage_fund_info:
                    fund_list = []
                    for f in manage_fund_info:
                        rank = f.get("rank")
                        totalRank = f.get("totalRank")
                        fmt_rank = ""
                        if rank and totalRank:
                            fmt_rank = f"{rank}/{totalRank}"

                        fund_list.append({
                            "mf_fund_name": f.get("fundName", ""),
                            "mf_fund_code": f.get("fundCode", ""),
                            "mf_hold_start_date": f.get("holdStartDate", ""),
                            "mf_hold_end_date": f.get("holdEndDate", ""),
                            "mf_hold_days": f.get("holdDays", ""),
                            "mf_yield_since": f.get("yieldSinces") + '%' if f.get("yieldSinces") else None,
                            "mf_yield_hs300": f.get("yieldHS300") + '%' if f.get("yieldHS300") else None,
                            "mf_is_position": EnumMapper.map_is_position(f.get("isPosition", "")),
                            "mf_rank": fmt_rank,
                        })
                    manager_info["manage_fund_list"] = fund_list

                managers.append(manager_info)

            fund.fund_managers = managers

            # 兼容：保留第一个基金经理名称
            if data and not fund.manager:
                fund.manager = data[0].get("personName", "")

    @staticmethod
    def _decode_html_entities(text: str) -> str:
        """解码HTML实体编码"""
        if not text:
            return text
        # 替换常见的HTML实体
        html_entities = {
            "&lt;": "<",
            "&gt;": ">",
            "&le;": "≤",
            "&ge;": "≥",
            "&amp;": "&",
            "&nbsp;": " ",
        }
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        return text

    @staticmethod
    def parse_rate(fund: FundData, data: dict):
        """解析费率数据 (API: /msps-fstore/ajs/fund/new/v2/queryFundTransRule.do)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        # API返回格式: 直接返回费率相关字段
        manage_rate = data.get("manageRate", "")
        fund.management_fee = f"{manage_rate}/年" if manage_rate else manage_rate

        tg_rate = data.get("tgRate", "")
        fund.custodian_fee = f"{tg_rate}/年" if tg_rate else tg_rate

        # 申购费率 - 格式化所有档位（解码HTML实体，用分号分隔）
        apply_buy_rate_list = data.get("applyBuyRateList", [])
        if apply_buy_rate_list and isinstance(apply_buy_rate_list, list):
            subscription_lines = []
            for item in apply_buy_rate_list:
                sub_section = FundDataParser._decode_html_entities(item.get("subSectionText", ""))
                rate = item.get("rate", "")
                discount = item.get("disCountRate", "")
                if discount:
                    subscription_lines.append(f"{sub_section} {rate}(折后：{discount})")
                else:
                    subscription_lines.append(f"{sub_section} {rate}")
            fund.subscription_fee = "; ".join(subscription_lines)

        # 赎回费率 - 格式化所有档位（解码HTML实体，用分号分隔）
        redeem_rate_list = data.get("redeemRateList", [])
        if redeem_rate_list and isinstance(redeem_rate_list, list):
            redemption_lines = []
            for item in redeem_rate_list:
                sub_section = FundDataParser._decode_html_entities(item.get("subSectionText", ""))
                rate = item.get("rate", "")
                redemption_lines.append(f"{sub_section} {rate}")
            fund.redemption_fee = "; ".join(redemption_lines)

        # 收费方式
        fund.fee_type_name = data.get("feeTypeName", "")

        # 销售服务费率
        sale_service_rate = data.get("saleServiceRate", "")
        fund.sale_service_rate = f"{sale_service_rate}/年" if sale_service_rate else sale_service_rate

        # 交易确认日期信息 - 合并为简洁格式
        fund_trans_flow = data.get("fundTransFlowDto", {})
        if fund_trans_flow:
            buy_date = fund_trans_flow.get("buyDate", "")
            confirm_date = fund_trans_flow.get("confirmDate", "")
            confirm_week_day = fund_trans_flow.get("confirmWeekDay", "")
            earnings_date = fund_trans_flow.get("earningsDate", "")
            earnings_week_day = fund_trans_flow.get("earningsWeekDay", "")

            sell_date = fund_trans_flow.get("sellDate", "")
            sell_confirm_date = fund_trans_flow.get("sellConfirmDate", "")
            sell_confirm_week_day = fund_trans_flow.get("sellConfirmWeekDay", "")
            sell_acc_date = fund_trans_flow.get("sellAccDate", "")
            sell_acc_week_day = fund_trans_flow.get("sellAccWeekDay", "")

            # 买入规则：今日15:00之前买入，06-11（星期三）查看份额，06-11（星期三）可查收益
            buy_rule = ""
            if buy_date and confirm_date:
                buy_rule = f"今日15:00之前买入，{confirm_date}（{confirm_week_day}）查看份额，{earnings_date}（{earnings_week_day}）可查收益"

            # 卖出规则：今日15:00之前卖出，06-12（星期四）确认，06-12（星期四）到账
            sell_rule = ""
            if sell_date and sell_confirm_date:
                sell_rule = f"今日15:00之前卖出，{sell_confirm_date}（{sell_confirm_week_day}）确认，{sell_acc_date}（{sell_acc_week_day}）到账"

            fund.trans_detail = {
                "buy_date": buy_rule,
                "sell_date": sell_rule,
            }

    @staticmethod
    def parse_holding(fund: FundData, data: dict):
        """解析持仓数据 (API: /msps-fstore/ajs/fund/new/queryAssetAllocation.do)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        # 资产配置
        asset_allocation = data.get("assetAllocationList", [])
        asset_config = {}
        if isinstance(asset_allocation, list):
            for item in asset_allocation:
                asset_name = item.get("assetName", "")
                asset_ratio = item.get("assetRatio", "")
                if asset_name:
                    asset_config[asset_name] = asset_ratio + "%" if asset_ratio else None

        # 股票持仓/十大重仓股
        stock_list = data.get("stockList", [])
        stock_list_detail = []
        if isinstance(stock_list, list):
            for item in stock_list:
                stock_list_detail.append({
                    "stk_code": item.get("positionCode", ""),
                    "stk_name": item.get("positionName", ""),
                    "stk_price": item.get("latestPrice", ""),
                    "stk_chg": item.get("chg") + '%' if item.get("chg") else None,
                    "stk_ratio": item.get("positionRatio", "") + '%' if item.get("positionRatio") else None
                })

        # 债券持仓
        bond_list_data = data.get("bondList", [])
        bond_list_detail = []
        if isinstance(bond_list_data, list):
            for item in bond_list_data:
                bond_list_detail.append({
                    "bond_code": item.get("positionCode", ""),
                    "bond_name": item.get("positionName", ""),
                    "bond_ratio": item.get("positionRatio") + '%' if item.get("positionRatio") else None
                })

        # 基金持仓
        fund_list_data = data.get("fundList", [])
        fund_list_detail = []
        if isinstance(fund_list_data, list):
            for item in fund_list_data:
                fund_list_detail.append({
                    "fund_code": item.get("positionCode", ""),
                    "fund_name": item.get("positionName", ""),
                    "fund_ratio": item.get("positionRatio") + '%' if item.get("positionRatio") else None
                })

        fund.holdings = {
            "asset_allocation": asset_config,
            "stock_list": stock_list_detail,
            "bond_list": bond_list_detail,
            "fund_list": fund_list_detail,
        }

    @staticmethod
    def parse_industry(fund: FundData, data: dict):
        """解析行业分布数据 (API: /msps-fstore/ajs/fund/new/queryAssetAllocation.do, assetType=2)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        # 行业配置 - 与资产配置格式相同，只是数据内容不同
        asset_allocation = data.get("assetAllocationList", [])
        industry_config = []
        if isinstance(asset_allocation, list):
            for item in asset_allocation:
                industry_config.append({
                    "industry_code": item.get("assetCode", ""),
                    "industry_name": item.get("assetName", ""),
                    "industry_ratio": item.get("assetRatio") + '%' if item.get("assetRatio") else None
                })

        # 合并到holdings中
        if hasattr(fund, 'holdings') and fund.holdings:
            fund.holdings["industry_allocation"] = industry_config
        else:
            fund.holdings = {"industry_allocation": industry_config}

    @staticmethod
    def parse_risk(fund: FundData, data: dict):
        """解析风险数据 (API: /msps-fstore/ajs/fund/new/queryFundDiagnoseAnalyse.do) - 包含产品评级"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        risk = {}

        # 解析technologyList数组
        technology_list = data if isinstance(data, list) else data.get("technologyList", [])
        if isinstance(technology_list, list):
            for item in technology_list:
                tech_name = item.get("technologyName", "")
                tech_value = item.get("technologyValue", "")
                ranking_num = item.get("rankingNum", "")
                total_num = item.get("totalNum", "")

                # 添加排名信息
                ranking_info = f"{ranking_num}/{total_num}" if ranking_num and total_num else ""

                if "波动率" in tech_name:
                    risk["volatility"] = tech_value
                    if ranking_info:
                        risk["volatility_rank"] = ranking_info
                elif "信息比率" in tech_name:
                    risk["information_ratio"] = tech_value
                    if ranking_info:
                        risk["information_ratio_rank"] = ranking_info
                elif "最大回撤" in tech_name:
                    risk["max_drawdown"] = tech_value
                    if ranking_info:
                        risk["max_drawdown_rank"] = ranking_info
                elif "索提诺比率" in tech_name:
                    risk["sortino_ratio"] = tech_value
                elif "卡玛比率" in tech_name:
                    risk["calmar_ratio"] = tech_value

        # 解析产品评级详情 prodRatingDetail
        prod_rating = data.get("prodRatingDetail", {}) if isinstance(data, dict) else {}
        if prod_rating:
            risk["composite_rating"] = EnumMapper.map_rating(prod_rating.get("compositeRating", ""))
            risk["anti_risk_capability"] = EnumMapper.map_rating(prod_rating.get("antiRiskCapability", ""))
            risk["profit_ability"] = EnumMapper.map_rating(prod_rating.get("profitAbility", ""))
            risk["stock_selection_ability"] = EnumMapper.map_rating(prod_rating.get("stockSelectionAbility", ""))
            risk["performance_stability"] = EnumMapper.map_rating(prod_rating.get("performanceStablity", ""))
            risk["reference_tracking_capability"] = EnumMapper.map_rating(
                prod_rating.get("referenceTrackingCapability", ""))
            risk["excess_earning_power"] = EnumMapper.map_rating(prod_rating.get("excessEarningPower", ""))

        fund.risk = risk

    @staticmethod
    def parse_base_info(fund: FundData, data: dict):
        """解析基金基本信息数据 (API: /msps-fstore/ajs/fund/new/queryFundBasicInfo.do)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        fund.establish_date = data.get("fundFoundDate", "")
        fund.custodian = data.get("fundTgName", "")

    @staticmethod
    def parse_simple_info(fund: FundData, data: dict):
        """解析基金基本信息数据 (API: /msps-fstore/ajs/fund/new/queryFundSimpleInfo.do)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        scale = data.get("fundNav", "")
        unit = data.get("fundNavUnit", "")
        fund.scale = f"{scale} {EnumMapper.SCALE_UNIT_MAP.get(unit)}" if scale and unit else None

        # 基金管理公司
        fund.manager = data.get("companyName", "")

    @staticmethod
    def parse_trend(fund: FundData, data: dict):
        """解析走势图数据 (API: /msps-fstore/ajs/fund/new/v1/queryFundTrend.do)"""
        if not data:
            return
        # 检查业务异常
        if is_business_error(data):
            fund.error = f"code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}"
            return

        # dataList数组: 每个元素包含 enddate, cumulativeAnvperRate(基金累计收益率), cumulativeHs300Rate(沪深300累计收益率)
        data_list = data.get("dataList", [])
        if not isinstance(data_list, list):
            return

        # 只保留走势图数据，不包含最大值最小值
        trend_data = []
        for item in data_list:
            trend_data.append({
                "date": item.get("enddate", ""),
                "fund_return": item.get("cumulativeAnvperRate", ""),
                "hs300_return": item.get("cumulativeHs300Rate", ""),
            })

        fund.trend = trend_data


# ==================== 基金数据查询器 ====================

class FundDataFetcher:
    """单只基金数据获取器"""

    def __init__(self, client: FundAPIClient):
        self.client = client

    async def fetch(self, code: str) -> dict:
        """获取单只基金完整数据"""
        fund = FundData(code)

        try:
            # 前置校验API Key，避免9个并行请求因Key缺失同时失败
            try:
                Config.API_KEY()
            except Exception as e:
                fund.error = f"API Key校验失败: {str(e)}"
                return fund.to_dict()

            # 获取基本信息
            detail = await self.client.get_fund_detail(code)
            if is_business_error(detail):
                fund.error = f"code: {detail.get('code')}, state: {detail.get('state')}, message: {detail.get('message')}"
                return fund.to_dict()
            elif detail and "error" not in detail:
                FundDataParser.parse_detail(fund, detail)

            # 并行获取其他数据（资产配置和行业分布分别获取）
            perf, mgr, rate, holding, industry, risk, base_info, simple_info, trend = await asyncio.gather(
                self.client.get_fund_performance(code),
                self.client.get_fund_manager(code),
                self.client.get_fund_rate(code),
                self.client.get_fund_holding(code, "1"),  # 资产配置
                self.client.get_fund_holding(code, "2"),  # 行业分布
                self.client.get_fund_risk(code),  # 完整风险数据
                self.client.get_fund_base_info(code),
                self.client.get_fund_simple_info(code),
                self.client.get_fund_trend(code),  # 走势图数据
                return_exceptions=True
            )

            # 检测业务异常和请求异常
            service_errors = []
            for name, data in [("业绩", perf), ("经理", mgr), ("费率", rate), ("持仓", holding),
                               ("行业", industry), ("风险", risk), ("基本信息", base_info),
                               ("简介", simple_info), ("走势", trend)]:
                if isinstance(data, Exception):
                    service_errors.append(f"{name}: 请求异常 ({type(data).__name__}: {str(data)})")
                elif is_business_error(data):
                    service_errors.append(f"{name}: code: {data.get('code')}, state: {data.get('state')}, message: {data.get('message')}")

            # 解析各维度数据（跳过业务异常的数据）
            if not isinstance(perf, Exception) and perf and not is_business_error(perf):
                FundDataParser.parse_performance(fund, perf)
            if not isinstance(mgr, Exception) and mgr and not is_business_error(mgr):
                FundDataParser.parse_manager(fund, mgr)
            if not isinstance(rate, Exception) and rate and not is_business_error(rate):
                FundDataParser.parse_rate(fund, rate)
            if not isinstance(holding, Exception) and holding and not is_business_error(holding):
                FundDataParser.parse_holding(fund, holding)
            # 合并行业分布数据
            if not isinstance(industry, Exception) and industry and not is_business_error(industry):
                FundDataParser.parse_industry(fund, industry)
            # 解析风险数据（包含产品评级详情）
            if not isinstance(risk, Exception) and risk and not is_business_error(risk):
                FundDataParser.parse_risk(fund, risk)
            if not isinstance(base_info, Exception) and base_info and not is_business_error(base_info):
                FundDataParser.parse_base_info(fund, base_info)
            if not isinstance(simple_info, Exception) and simple_info and not is_business_error(simple_info):
                FundDataParser.parse_simple_info(fund, simple_info)
            if not isinstance(trend, Exception) and trend and not is_business_error(trend):
                FundDataParser.parse_trend(fund, trend)

            # 记录服务异常信息
            if service_errors:
                fund.error = "; ".join(service_errors)
                # 将请求异常单独写入fetch_errors（结构化错误提示）
                fund.fetch_errors = [e for e in service_errors if "请求异常" in e]

            # 获取基金经理详细信息
            await self._fetch_manager_detail(fund)

        except Exception as e:
            fund.error = str(e)

        return fund.to_dict()

    async def _fetch_manager_detail(self, fund: FundData):
        """获取基金经理详细信息并合并到fund_managers中"""
        if not fund.fund_managers:
            return

        # 并行获取所有基金经理的详情
        async def fetch_single(manager: dict) -> dict:
            manager_code = manager.get("code")
            if not manager_code:
                return manager
            try:
                detail = await self.client.get_fund_manager_detail(manager_code)
                if detail and "error" not in detail:
                    manager.update({
                        "company": detail.get("fundCompany", ""),
                        "management_scale": detail.get("managementScale") + '亿' if detail.get(
                            "managementScale") else None,
                        "service_year": detail.get("serviceYear", ""),
                        "annual_yield": detail.get("annualYield") + '%' if detail.get("annualYield") else None,
                        "synopsis": detail.get("synopsis", ""),
                    })
            except Exception:
                pass
            return manager

        # 并行获取所有基金经理详情
        fund.fund_managers = await asyncio.gather(
            *[fetch_single(m) for m in fund.fund_managers]
        )


# ==================== 主程序 ====================

async def get_fund_data(fund_code: str) -> dict:
    """
    获取单只基金数据

    Args:
        fund_code: 基金代码

    Returns:
        dict: 基金数据JSON，包含meta.field_mapping字段映射说明
    """
    client = FundAPIClient(Config.BASE_URL)
    try:
        fetcher = FundDataFetcher(client)
        result = await fetcher.fetch(fund_code)

        result["timestamp"] = datetime.now().isoformat()

        # 添加字段映射文档（不进行字段名中文替换）
        result["meta"] = {
            "field_mapping": FieldMapper.get_field_mapping(),
            "data_source": "国投证券",
        }

        return result

    finally:
        await client.close()


async def get_fund_risk_detail(fund_code: str) -> dict:
    """
    获取基金风险指标详细信息（包括产品评级详情）

    Args:
        fund_code: 基金代码

    Returns:
        dict: 包含prod_rating_detail和technologyList
    """
    client = FundAPIClient(Config.BASE_URL)
    try:
        url = f"{client.base_url}{Config.ROUTES['fund_risk']}"
        resp = await client.client.post(url, params=client._params(fundCode=fund_code), headers=client._headers())
        data = client._parse_json(resp)
        # 检查 HTTP 状态码，如果是错误状态则返回原始响应
        if resp.status_code >= 400:
            return data
        return data.get("data", {}) if data.get("data") else {}
    finally:
        await client.close()


async def get_manager_data(manager_code: str) -> dict:
    """
    根据基金经理代码查询基金经理详细信息

    Args:
        manager_code: 基金经理代码

    Returns:
        dict: 基金经理详细信息JSON，包含meta.field_mapping字段映射说明
    """
    client = FundAPIClient(Config.BASE_URL)
    try:
        result = await client.get_fund_manager_detail(manager_code)

        if result:
            result["timestamp"] = datetime.now().isoformat()

        # 添加字段映射文档（不进行字段名中文替换）
        if result:
            result["meta"] = {
                "field_mapping": FieldMapper.get_field_mapping(),
                "data_source": "国投证券",
            }

        return result or {"error": "未找到基金经理信息"}

    finally:
        await client.close()


def _get_default_output_dir() -> Path:
    """返回默认输出目录路径（当前skill根目录下的.output子目录）。"""
    script_dir = Path(__file__).resolve().parent
    # 向上一级: scripts -> sdicsc-fund-query-compare (skill根目录)
    skill_dir = script_dir.parent
    return skill_dir / ".output"


def main():
    parser = argparse.ArgumentParser(description="基金数据查询工具")
    parser.add_argument("--fund", help="基金代码")
    parser.add_argument("--manager", help="基金经理代码")
    parser.add_argument("--output", default=None, help="输出文件路径")
    args = parser.parse_args()

    # 执行查询
    if args.manager:
        # 根据基金经理代码查询
        result = asyncio.run(get_manager_data(args.manager))
    elif args.fund:
        # 根据基金代码查询
        result = asyncio.run(get_fund_data(args.fund))
    else:
        parser.print_help()
        return

    # 输出
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"数据已保存至: {output_path}")
    else:
        # 默认保存到隐藏目录
        output_dir = _get_default_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        # 使用时间戳生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"fund_{timestamp}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"数据已保存至: {output_path}")


if __name__ == "__main__":
    main()
