#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日热点选题（付费版）【零一数科·出品】 —— 联网主脚本 (v0.1.0)

异步任务模型：
  读 Key → 校验参数 → POST /api/v1/content/hot-daily/tasks（立即返回 task_id）→
  GET /tasks/{id} 轮询进度（stderr 输出）→ 终态后提取 billing.total_points →
  取 data.markdown → 写盘 → 分隔符协议输出 stdout。

失败可按 task_id 调用 POST /tasks/{id}/retry（异步，再轮询；已成功不重跑）。
退出码见 SKILL.md「退出码处理」。纯标准库。
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# --------------------------------------------------------------------------- 常量
BASE_URL = "https://claw.lingyishuke.com/services"
TASKS_PATH = "/api/v1/content/hot-daily/tasks"

DEFAULT_TIMEOUT = 90   # 单次轮询等待上限（秒）；< WorkBuddy/Web 单轮上限；到点不 fail，emit 进行中后退出 13，可续轮询
HTTP_TIMEOUT = 60      # 单次 HTTP 超时（创建/retry/get）
HTTP_RETRY_TIMES = 4
MAX_BACKOFF = 8
PROGRESS_POLL_INTERVAL = 5

# 约定回退扣点（仅「约 N 点」提示，不当作实扣；示例 8 选题约扣 12 点）
PLAN_POINTS = 12

GOALS = {"种草", "带货", "品宣", "引私域"}
PLATFORMS = {"douyin", "xiaohongshu", "weibo", "kuaishou", "zhihu"}
INDUSTRY_MAX_LEN = 64
ADDITIONAL_MAX_LEN = 2000
COUNT_MIN, COUNT_MAX, COUNT_DEFAULT = 5, 10, 8
IDEMPOTENCY_MAX_LEN = 128

# 任务态
STATUS_OK = "succeeded"
STATUS_TERMINAL = frozenset({"succeeded", "failed", "billing_failed"})
STATUS_RETRYABLE = frozenset({"failed", "billing_failed"})

# 退出码
E_OK = 0
E_NO_KEY = 2
E_PARAM = 3
E_BALANCE = 4
E_AUTH = 8
E_4XX = 10
E_5XX = 11
E_FAILED = 12   # 已发起但中途失败
E_PENDING = 13  # 已发起但未到终态（非失败，可续 --poll-task）

# stdout 交付协议
PREFIX = "HOT_DAILY"
POINTS_PREFIX = "%s_POINTS_USED=" % PREFIX
PLAN_PREFIX = "%s_PLAN_POINTS=" % PREFIX
REPORT_START = "=== %s_REPORT_START ===" % PREFIX
REPORT_END = "=== %s_REPORT_END ===" % PREFIX
FILE_PREFIX = "%s_REPORT_FILE=" % PREFIX
TASK_PREFIX = "%s_TASK_ID=" % PREFIX
STATUS_PREFIX = "%s_STATUS=" % PREFIX
PROGRESS_PREFIX = "%s_PROGRESS=" % PREFIX
EAPSED_PREFIX = "%s_EAPSED=" % PREFIX

if os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = ssl.create_default_context()


# --------------------------------------------------------------------------- 工具
def log(msg):
    print("[hot_daily] %s" % msg, file=sys.stderr, flush=True)


def fail(code, msg):
    log("❌ " + msg)
    sys.exit(code)


def to_text(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except Exception:
            return value.decode("utf-8", "ignore")
    return value


def get_api_key():
    """从技能目录 config.json 读 LY_API_KEY，回退环境变量。"""
    skill_dir = Path(__file__).resolve().parent.parent
    cfg = skill_dir / "config.json"
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text("utf-8"))
            if isinstance(data, dict) and data.get("LY_API_KEY"):
                return to_text(data["LY_API_KEY"]).strip()
        except (json.JSONDecodeError, OSError):
            pass
    env = os.environ.get("LY_API_KEY")
    return env.strip() if env else ""


def auth_headers(api_key, idempotency_key=None):
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "X-Appbuilder-From": "openclaw",
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
    }
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    return headers


def parse_json(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def http_request(url, method, headers, body, timeout):
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read()
            return status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            raw = e.read()
        except Exception:
            raw = b""
        return status, raw.decode("utf-8", "ignore")


def http_request_with_retries(url, method, headers, body, timeout, label, retries=HTTP_RETRY_TIMES):
    """瞬时网络错误 / 5xx 有限重试；4xx 直接返回。"""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            status, text = http_request(url, method, headers, body, timeout)
            if status >= 500 and attempt < retries:
                wait = min(2 ** (attempt - 1), MAX_BACKOFF)
                log("%s服务端 %s，%ds 后重试（%d/%d）" % (label, status, wait, attempt, retries))
                time.sleep(wait)
                continue
            return status, text
        except urllib.error.URLError as e:
            last_err = e
            if attempt >= retries:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s网络错误：%s，%ds 后重试（%d/%d）" % (label, e, wait, attempt, retries))
            time.sleep(wait)
        except Exception as e:
            last_err = e
            if attempt >= retries:
                break
            wait = min(2 ** (attempt - 1), MAX_BACKOFF)
            log("%s请求异常：%s，%ds 后重试（%d/%d）" % (label, e, wait, attempt, retries))
            time.sleep(wait)
    raise last_err


# --------------------------------------------------------------------------- 扣点提取
def extract_total_points(payload):
    """提取正式扣点字段 billing.total_points。优先 data.billing.total_points，
    回退历史候选 key。命中返回数值，否则 None。"""
    if not isinstance(payload, dict):
        return None

    def _as_number(val):
        if isinstance(val, bool):
            return None
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str) and val.strip():
            try:
                f = float(val.strip())
                return int(f) if f.is_integer() else f
            except ValueError:
                return None
        return None

    candidates = []
    data = payload.get("data")
    if isinstance(data, dict):
        billing = data.get("billing")
        if isinstance(billing, dict):
            candidates.append(billing.get("total_points"))
        candidates.append(data.get("total_points"))
    billing_top = payload.get("billing")
    if isinstance(billing_top, dict):
        candidates.append(billing_top.get("total_points"))
    candidates.append(payload.get("total_points"))

    for c in candidates:
        n = _as_number(c)
        if n is not None:
            return n

    legacy_keys = ("points_used", "credits_used", "used_points", "deducted_points",
                   "charged_points", "points_cost", "point_used", "consumed_points")
    levels = [payload]
    if isinstance(data, dict):
        levels.append(data)
        for sub in ("billing", "result", "payment", "cost", "usage"):
            sub_obj = data.get(sub)
            if isinstance(sub_obj, dict):
                levels.append(sub_obj)
    for sub in ("billing", "payment", "cost", "usage"):
        sub_obj = payload.get(sub)
        if isinstance(sub_obj, dict):
            levels.append(sub_obj)
    for level in levels:
        for key in legacy_keys:
            if key in level:
                n = _as_number(level[key])
                if n is not None:
                    return n
    return None


def extract_recharge(payload):
    if not isinstance(payload, dict):
        return None
    inner = payload.get("data")
    if isinstance(inner, dict) and inner.get("recharge_url"):
        return inner.get("recharge_url")
    return payload.get("recharge_url")


def fmt_points(value):
    if value is None or isinstance(value, bool):
        return ""
    try:
        f = float(value)
        return str(int(f)) if f.is_integer() else str(f)
    except (TypeError, ValueError):
        return str(value)


# --------------------------------------------------------------------------- HTTP 错误分流
def raise_for_http(status, payload, resp_text, label):
    msg = ""
    if isinstance(payload, dict):
        msg = (payload.get("message")
               or (payload.get("detail") if isinstance(payload.get("detail"), str) else None)
               or "")
        detail = payload.get("detail")
        if isinstance(detail, dict) and detail.get("message"):
            msg = detail.get("message") or msg
    if not msg:
        msg = (resp_text or "")[:200]

    if status == 401:
        fail(E_AUTH, "%s鉴权失败（HTTP 401）：API Key 无效或已过期，请更新 config.json 的 LY_API_KEY。服务端：%s" % (label, msg))
    if status == 402:
        recharge = extract_recharge(payload or {})
        tip = "%s余额不足，无法调用。" % label
        if recharge:
            tip += " 请前往充值：%s" % recharge
        fail(E_BALANCE, tip)
    if status in (400, 422):
        fail(E_PARAM, "%s参数/校验失败（HTTP %s）：%s" % (label, status, msg))
    if status == 404:
        fail(E_4XX, "%s任务不存在或不属于当前账号（HTTP 404）：%s" % (label, msg))
    if 400 <= status < 500:
        fail(E_4XX, "%s调用失败（HTTP %s）：%s" % (label, status, msg))
    if status >= 500:
        fail(E_5XX, "%s服务端错误（HTTP %s）：%s" % (label, status, msg or "Internal server error"))


# --------------------------------------------------------------------------- 调任务 API
def _parse_task_response(status, resp_text, label):
    payload = parse_json(resp_text)
    if status != 200:
        raise_for_http(status, payload, resp_text, label)
    if payload is None:
        fail(E_5XX, "%s返回非 JSON（HTTP %s）：%s" % (label, status, resp_text[:200]))
    if payload.get("result") != "success":
        fail(E_4XX, "%s失败：HTTP %s result=%s message=%s" % (label, status, payload.get("result"), payload.get("message")))
    data = payload.get("data")
    if not isinstance(data, dict):
        fail(E_FAILED, "%s返回 data 为空或非对象。" % label)
    return data, payload


def _progress_summary(data):
    """从任务 data 汇总人类可读进度文案。本 API 无 current_module，按 status/billing_status 推断。"""
    status = str(data.get("status") or "")
    billing_status = str(data.get("billing_status") or "")
    failure = data.get("failure_message") or ""
    if status == "pending":
        return "任务排队中，等待执行"
    if status == "running":
        return "热点采集与选题生成中"
    if status in STATUS_TERMINAL:
        if status == STATUS_OK:
            return "已完成"
        return "已结束：%s%s" % (status, ("（%s）" % failure) if failure else "")
    return "status=%s%s" % (status, (" billing=%s" % billing_status) if billing_status else "")


def log_task_progress(data, elapsed=None, prefix="进度", emit_task_id=False):
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    summary = _progress_summary(data)
    elapsed_s = ""
    if elapsed is not None:
        elapsed_s = " elapsed=%ds" % int(elapsed)
    log("%s：status=%s%s task_id=%s | %s" % (prefix, status or "?", elapsed_s, task_id or "-", summary))
    if emit_task_id and task_id:
        print("[hot_daily] %s%s" % (TASK_PREFIX, task_id), file=sys.stderr, flush=True)


def call_create_task(base_url, api_key, body_obj, idempotency_key, timeout, label="创建热点日报任务"):
    url = base_url.rstrip("/") + TASKS_PATH
    body_obj = dict(body_obj)
    body_obj["idempotency_key"] = idempotency_key
    body = json.dumps(body_obj, ensure_ascii=False)
    log("%s：industry=%s goal=%s count=%s key=%s"
        % (label, body_obj.get("industry"), body_obj.get("goal"), body_obj.get("count"), idempotency_key[:8] + "…"))
    try:
        status, resp_text = http_request_with_retries(
            url, "POST", auth_headers(api_key, idempotency_key), body, timeout, label)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s（请检查网络与服务可达性：%s）" % (label, e, base_url))
    return _parse_task_response(status, resp_text, label)


def call_get_task(base_url, api_key, task_id, timeout, label="查询热点日报任务"):
    url = base_url.rstrip("/") + TASKS_PATH + "/" + task_id
    try:
        status, resp_text = http_request_with_retries(
            url, "GET", auth_headers(api_key), None, timeout, label, retries=2)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def call_retry_task(base_url, api_key, task_id, timeout, label="重试热点日报任务"):
    url = base_url.rstrip("/") + TASKS_PATH + "/" + task_id + "/retry"
    log("%s：task_id=%s" % (label, task_id))
    try:
        status, resp_text = http_request_with_retries(
            url, "POST", auth_headers(api_key), None, timeout, label)
    except Exception as e:
        fail(E_5XX, "%s网络错误：%s" % (label, e))
    return _parse_task_response(status, resp_text, label)


def wait_for_task(base_url, api_key, data, payload, timeout_total, poll_interval=PROGRESS_POLL_INTERVAL):
    """轮询 GET 直到终态或单次超时。返回 (data, payload, exit_code)：
    终态 E_OK；单次轮询到上限 E_PENDING（非失败）。"""
    if not isinstance(data, dict):
        fail(E_FAILED, "任务响应 data 无效，无法轮询。")
    status = str(data.get("status") or "")
    task_id = str(data.get("task_id") or "")
    started = time.time()
    log_task_progress(data, elapsed=0, prefix="任务已提交", emit_task_id=True)

    if status in STATUS_TERMINAL:
        return data, payload, E_OK
    if not task_id:
        fail(E_FAILED, "创建任务未返回 task_id，无法轮询进度。")

    log("开始轮询任务进度（间隔 %ds，单次最长 %ds）…" % (poll_interval, int(timeout_total)))
    while True:
        elapsed = time.time() - started
        if elapsed >= timeout_total:
            log("单次轮询到上限（%ds）：仍非终态，可续轮询。" % int(timeout_total))
            return data, payload, E_PENDING
        time.sleep(poll_interval)
        try:
            data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        except SystemExit:
            raise
        except Exception as e:
            log("轮询暂失败：%s（将继续）" % e)
            continue
        status = str(data.get("status") or "")
        log_task_progress(data, elapsed=time.time() - started, prefix="进度")
        if status in STATUS_TERMINAL:
            log("任务到达终态：status=%s task_id=%s" % (status, task_id))
            return data, payload, E_OK


# --------------------------------------------------------------------------- 结果提取与报告拼装
def extract_markdown(data):
    """从终态 data 取报告 markdown 字符串。本 API 为单一报告：data.markdown（顶层字符串）。
    兼容 data.result.markdown / data.data.markdown 嵌套形态。取不到返回 ""。"""
    if isinstance(data, dict):
        mk = data.get("markdown")
        result = data.get("result") if isinstance(data.get("result"), dict) else None
        if not mk and isinstance(result, dict):
            mk = result.get("markdown")
        if mk:
            return str(mk).strip()
    return ""


def make_title(industry):
    """报告一级标题用行业名。industry 已校验非空。"""
    name = str(industry or "").replace("\n", " ").strip()
    return name or "热点日报"


def assemble_report(industry, markdown):
    """拼最终报告 markdown。本后端已返回完整 markdown（含 # 一级标题），脚本不二次加工，只做兜底。"""
    md = (markdown or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not md:
        return "# 热点日报：%s\n\n报告正文为空。\n" % make_title(industry)
    # 后端 markdown 已自带标题，原样落盘；若缺一级标题则补一个
    if not md.lstrip().startswith("#"):
        md = "# 热点日报：%s\n\n%s\n" % (make_title(industry), md)
    return md


def plan_points_for():
    return PLAN_POINTS


def handle_task_outcome(data, payload, industry):
    """根据任务 status 产出报告或 fail。返回 (final_md, points, task_id)。"""
    task_id = str(data.get("task_id") or "")
    status = str(data.get("status") or "")
    failure_code = data.get("failure_code") or ""
    failure_message = data.get("failure_message") or data.get("failure_code") or ""

    points = extract_total_points(payload)
    if points is None:
        points = extract_total_points({"data": data})

    if status == STATUS_OK:
        md = extract_markdown(data)
        if md:
            return assemble_report(industry, md), points, task_id
        fail(E_FAILED, "任务成功但 markdown 为空：task_id=%s（可用 --retry-task 重试）" % task_id)

    # 本 API 无 partial_failed；但 billing_failed 可能已有 markdown
    if status == "billing_failed":
        md = extract_markdown(data)
        if md:
            log("结算失败但已有日报内容 status=billing_failed，先交付已有内容并提示。failure=%s" % failure_code)
            # 仍交付报告，但扣点未结算成功——不在此判定点数返还，由 SKILL 退出码话术统一说明
            return assemble_report(industry, md), points, task_id
        fail(E_FAILED, "日报内容已生成但结算失败：%s task_id=%s（请稍后重试或联系支持，可 --retry-task）" % (failure_message, task_id))

    # billing_failed 之外的失败码（HOT_DAILY_FAILED / ATTEMPTS_EXCEEDED / MISSING_ACCOUNT）
    detail = failure_message or failure_code or status or "unknown"
    if failure_code == "ATTEMPTS_EXCEEDED":
        fail(E_FAILED, "已达到服务端最大尝试次数（ATTEMPTS_EXCEEDED）：%s task_id=%s（停止自动重试，转人工排查）" % (detail, task_id))
    if failure_code == "MISSING_ACCOUNT":
        fail(E_AUTH, "任务缺少有效账号信息（MISSING_ACCOUNT）：请检查 config.json 的 LY_API_KEY 与账号配置。task_id=%s" % task_id)
    tip = "热点日报任务未成功：status=%s %s task_id=%s" % (status, detail, task_id)
    if task_id and failure_code != "ATTEMPTS_EXCEEDED":
        tip += "。可用 --retry-task %s 重试。" % task_id
    fail(E_FAILED, tip)


# --------------------------------------------------------------------------- 参数校验与 body 构造
def parse_csv_list(raw):
    if raw is None:
        return None
    tokens = [t.strip() for t in raw.split(",") if t.strip()]
    return tokens if tokens else []


def build_body(args, industry):
    """按 references/api.md 构造 POST 创建任务 body。"""
    body = {"industry": industry}
    bk = parse_csv_list(args.brand_keywords)
    if bk:
        body["brand_keywords"] = bk
    if args.platforms:
        body["platforms"] = args.platforms
    if args.goal:
        body["goal"] = args.goal
    if args.count is not None:
        body["count"] = args.count
    if args.additional_requirements:
        body["additional_requirements"] = args.additional_requirements
    return body


def validate_inputs(industry, args):
    """校验业务参数，非法→退出码 3。"""
    industry = (industry or "").strip()
    if not industry:
        fail(E_PARAM, "行业名称不能为空（1～64 字符）。")
    if len(industry) > INDUSTRY_MAX_LEN:
        fail(E_PARAM, "行业名称超过 %d 字符上限（当前 %d）。" % (INDUSTRY_MAX_LEN, len(industry)))

    if args.goal and args.goal not in GOALS:
        fail(E_PARAM, "营销目标 goal 必须是 %s 之一，当前：%s" % ("、".join(sorted(GOALS)), args.goal))

    if args.count is not None and not (COUNT_MIN <= args.count <= COUNT_MAX):
        fail(E_PARAM, "选题数量 count 须在 %d～%d 之间，当前：%s" % (COUNT_MIN, COUNT_MAX, args.count))

    if args.additional_requirements and len(args.additional_requirements) > ADDITIONAL_MAX_LEN:
        fail(E_PARAM, "额外要求超过 %d 字符上限（当前 %d）。" % (ADDITIONAL_MAX_LEN, len(args.additional_requirements)))

    if args.platforms:
        bad = [p for p in args.platforms if p not in PLATFORMS]
        if bad:
            fail(E_PARAM, "platforms 含非法值：%s。可选：%s" % ("、".join(bad), "、".join(sorted(PLATFORMS))))

    if args.idempotency_key and len(args.idempotency_key) > IDEMPOTENCY_MAX_LEN:
        fail(E_PARAM, "幂等键超过 %d 字符上限（当前 %d）。" % (IDEMPOTENCY_MAX_LEN, len(args.idempotency_key)))

    return industry


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="每日热点选题（异步任务 API · v0.1.0）")
    ap.add_argument("--industry", default=None, help="行业名称，1～64 字符（必填）")
    ap.add_argument("--brand-keywords", default=None, help="品牌或产品关键词 CSV，如 '兰蔻,小棕瓶'")
    ap.add_argument("--platforms", default=None,
                    help="平台过滤 CSV，如 'douyin,xiaohongshu'；可选：douyin/xiaohongshu/weibo/kuaishou/zhihu")
    ap.add_argument("--goal", default=None, help="营销目标：种草/带货/品宣/引私域，默认种草")
    ap.add_argument("--count", type=int, default=None, help="期望选题数量，5～10，默认 8")
    ap.add_argument("--additional-requirements", default=None, help="额外要求，最多 2000 字符")
    ap.add_argument("--out", default=None, help="输出 MD 路径；缺省写当前目录的 热点日报-<task_id>.md")
    ap.add_argument("--insecure", action="store_true", help="跳过 SSL 校验")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="单次轮询等待上限秒数（默认 %s，< WorkBuddy/Web 单轮上限）。到点非错误，进行中退出 13 可续轮询。" % DEFAULT_TIMEOUT)
    ap.add_argument("--poll-interval", type=float, default=PROGRESS_POLL_INTERVAL,
                    help="进度轮询间隔秒数，默认 %s" % PROGRESS_POLL_INTERVAL)
    ap.add_argument("--idempotency-key", default=None, help="幂等键；缺省自动生成 UUID。重复提交同一任务请保持不变。")
    ap.add_argument("--retry-task", default=None, metavar="TASK_ID", help="对已有 task_id 调用 POST /retry，跳过 --industry")
    ap.add_argument("--only-create", action="store_true", help="仅 POST 创建拿 task_id 后即退（退出码 0，不轮询）")
    ap.add_argument("--poll-task", default=None, metavar="TASK_ID",
                    help="对已有 task_id 执行 GET 轮询；务必带 --industry（用于报告标题）。终态交付(exit0)；仍运行 exit13；终态失败 exit12。")
    # --poll-task / --retry-task 模式下仍带 --industry 仅用于报告标题兜底（后端 markdown 已自带标题）
    args = ap.parse_args()

    api_key = get_api_key()
    if not api_key:
        fail(E_NO_KEY, "未取到 API Key：技能目录 config.json 不存在或无 LY_API_KEY 字段。\n"
              "请前往 https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy 获取，\n"
              "写入 config.json（如 {\"LY_API_KEY\": \"你的密钥\"}）或设环境变量 LY_API_KEY 后重试。")

    if args.insecure or os.environ.get("LY_SKIP_SSL_VERIFY") == "1":
        global SSL_CONTEXT
        SSL_CONTEXT = ssl.create_default_context()
        SSL_CONTEXT.check_hostname = False
        SSL_CONTEXT.verify_mode = ssl.CERT_NONE

    base_url = os.environ.get("LY_BASE_URL", BASE_URL)
    poll_interval = max(1.0, float(args.poll_interval or PROGRESS_POLL_INTERVAL))

    # 预解析 --platforms
    if args.platforms:
        args.platforms = parse_csv_list(args.platforms)

    # —— 轮询已有任务 ——
    if args.poll_task:
        task_id = args.poll_task.strip()
        if not task_id:
            fail(E_PARAM, "--poll-task 不能为空。")
        data, payload = call_get_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        status = str(data.get("status") or "")
        if status not in STATUS_TERMINAL:
            data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        else:
            code = E_OK
        status = str(data.get("status") or "")
        if status in STATUS_TERMINAL:
            industry_for_title = (args.industry or "").strip() or ("任务 %s" % task_id[:8])
            if not (args.industry or "").strip():
                log("提示：--poll-task 未带 --industry，报告标题用后端 markdown 自带标题；建议带上 --industry。")
            final_md, used_points, task_id_out = handle_task_outcome(data, payload, industry_for_title)
            _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
            return
        _emit_pending(data, task_id, int(args.timeout))
        return

    # —— 重试模式 ——
    if args.retry_task:
        task_id = args.retry_task.strip()
        if not task_id:
            fail(E_PARAM, "--retry-task 不能为空。")
        data, payload = call_retry_task(base_url, api_key, task_id, HTTP_TIMEOUT)
        data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
        if code == E_PENDING:
            _emit_pending(data, task_id, int(args.timeout))
            return
        industry_for_title = (args.industry or "").strip() or ("任务 %s" % task_id[:8])
        final_md, used_points, task_id_out = handle_task_outcome(data, payload, industry_for_title)
        _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)
        return

    # —— 仅创建任务（创建后即退，不轮询）——
    if args.only_create:
        if not args.industry:
            fail(E_PARAM, "--only-create 仍需 --industry 提供行业名称。")
        industry = validate_inputs(args.industry, args)
        body = build_body(args, industry)
        idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
        data, payload = call_create_task(base_url, api_key, body, idem, HTTP_TIMEOUT)
        task_id = str(data.get("task_id") or "")
        status = str(data.get("status") or "")
        summary = _progress_summary(data)
        print(TASK_PREFIX + task_id)
        print(STATUS_PREFIX + status)
        print(PROGRESS_PREFIX + summary)
        print(REPORT_START)
        print(REPORT_END)
        sys.stdout.flush()
        log("已创建任务（仅创建模式）：task_id=%s status=%s" % (task_id, status))
        sys.exit(E_OK)

    # —— 新建任务 ——
    if not args.industry:
        fail(E_PARAM, "请提供 --industry，或使用 --retry-task <task_id> 或 --poll-task <task_id>。")
    industry = validate_inputs(args.industry, args)
    body = build_body(args, industry)
    idem = (args.idempotency_key or "").strip() or str(uuid.uuid4())
    log("将创建任务，industry=%s goal=%s count=%s" % (industry, body.get("goal", "种草"), body.get("count", COUNT_DEFAULT)))
    data, payload = call_create_task(base_url, api_key, body, idem, HTTP_TIMEOUT)
    data, payload, code = wait_for_task(base_url, api_key, data, payload, args.timeout, poll_interval)
    if code == E_PENDING:
        _emit_pending(data, str(data.get("task_id") or ""), int(args.timeout))
        return
    final_md, used_points, task_id_out = handle_task_outcome(data, payload, industry)
    _emit(final_md, used_points, plan_points_for(), args.out, task_id_out)


def _emit_pending(data, task_id, elapsed):
    """单次轮询未到终态：透出进行中状态，退出码 E_PENDING（非失败，可续轮询）。"""
    status = str(data.get("status") or "")
    summary = _progress_summary(data)
    print(TASK_PREFIX + (task_id or ""))
    print(STATUS_PREFIX + status)
    print(PROGRESS_PREFIX + summary)
    print(EAPSED_PREFIX + "%d" % int(elapsed or 0))
    print(REPORT_START)
    print(REPORT_END)
    sys.stdout.flush()
    log("进行中：status=%s task_id=%s elapsed=%ds，可续 --poll-task。" % (status, task_id or "-", int(elapsed or 0)))
    sys.exit(E_PENDING)


def _safe_filename_stem(task_id):
    return "".join(c for c in str(task_id or "") if c.isalnum() or c in "-_") or uuid.uuid4().hex


def _write_report_to_disk(final_md, out_path, task_id):
    """三级兜底确保必生成 md：--out → 当前目录 热点日报-<id>.md → /tmp/热点日报-<id>.md。"""
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / "热点日报.md"
        candidates.append(p)
    stem = _safe_filename_stem(task_id)
    candidates.append(Path.cwd() / ("热点日报-%s.md" % stem))
    candidates.append(Path("/tmp") / ("热点日报-%s.md" % stem))

    last_err = None
    for p in candidates:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(final_md, "utf-8")
            md_path = str(p.resolve())
            log("报告已写入：%s" % md_path)
            return md_path
        except OSError as e:
            last_err = e
            log("写盘失败（%s），尝试下一兜底路径…" % p)
            continue
        except Exception as e:
            last_err = e
            log("写盘异常（%s）：%s，尝试下一兜底路径…" % (p, e))
            continue
    log("⚠️ 所有写盘路径均失败：%s（报告正文已通过 stdout 交付，可手动保存）" % last_err)
    return ""


def _emit(final_md, used_points, plan_total, out_path, task_id):
    md_path = _write_report_to_disk(final_md, out_path, task_id)
    points_str = fmt_points(used_points)
    print(POINTS_PREFIX + points_str)
    print(PLAN_PREFIX + str(plan_total))
    print(FILE_PREFIX + md_path)
    print(TASK_PREFIX + (task_id or ""))
    print(REPORT_START)
    sys.stdout.write(final_md)
    if not final_md.endswith("\n"):
        sys.stdout.write("\n")
    print(REPORT_END)
    sys.stdout.flush()
    log("完成。task_id=%s points=%s" % (task_id or "-", points_str or "(empty)"))
    sys.exit(E_OK)


if __name__ == "__main__":
    main()
