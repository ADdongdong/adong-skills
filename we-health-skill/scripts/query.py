#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微医健康技能 — 健康查询脚本。

支持场景：报告解读、医生/医院/科室推荐、健康咨询、用药咨询、药盒识别、饮食分析。

用法:
  python3 query.py "用户的健康问题"                    # 纯文本查询
  python3 query.py "用户问题" --region 北京            # 带地区查询
  python3 query.py "用户问题" --no-followup            # 跳过追问直接解读（报告解读场景必传）
  python3 query.py --stdin << 'EOF'                    # stdin JSON 模式
  {"query":"...","region":"北京","file_list":[...],"no_followup":true}
  EOF

注：--no-followup / no_followup 仅在 query 末尾追加「直接解读」跳过追问关键词，
不作为 API 参数发送。报告解读场景每次调用必须传入；健康管理方案等其他场景禁止传入。

API Key 无需用户配置：本地已存直接使用（credential.py 管理），
缺失或失效时自动通过设备机器码兑换注册（auth.py），新用户无感使用。

PDF 不经本脚本传输：AI 应先读取 PDF 提取文字内容，将文本直接拼入 query 后调用本脚本。
file_list 仅接受图片（pic）附件。

版本检查内置：每次查询成功后自动执行一次版本检查（后置、静默、默认 3 天（72 小时）节流），
检测到本地版本落后时向 stderr 输出一行 `[WY_UPDATE] UPDATE_AVAILABLE local=x remote=y`。
该行不是错误（退出码仍为 0），仅用于上层在回答末尾追加固定升级提示。

首次注册告知：本次查询若触发了机器码自动注册，成功后向 stderr 输出一行
`[WY_AUTH] REGISTERED`（同样不是错误），供上层在回答末尾追加一次告知。
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

# 同目录导入 auth 模块（内部经 credential 管理凭证存储）
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
auth = importlib.import_module("auth")

# ── 配置 ──────────────────────────────────────────────

API_URL = "https://aichat.guahao.com/chat/v1/wecare/skills/api/workbuddy/chat"
TIMEOUT_SECONDS = 120

# Windows 下强制 UTF-8 输出
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        _reconfigure = getattr(_stream, "reconfigure", None)
        if _reconfigure is not None:
            _reconfigure(encoding="utf-8", errors="replace")


# ── 参数解析 ──────────────────────────────────────────

def parse_args() -> dict[str, Any]:
    args = sys.argv[1:]
    result: dict[str, Any] = {
        "query": "", "file_list": None, "use_stdin": False,
        "region": "", "no_followup": False,
    }

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--stdin":
            result["use_stdin"] = True
        elif arg == "--no-followup":
            result["no_followup"] = True
        elif arg == "--region":
            if i + 1 < len(args):
                result["region"] = args[i + 1]
                i += 1
        elif arg.startswith("--region="):
            result["region"] = arg[len("--region="):]
        elif not arg.startswith("--") and not result["query"]:
            result["query"] = arg
        i += 1
    return result


# ── 验证 ──────────────────────────────────────────────

def validate_file_list(file_list: Any) -> tuple[bool, str]:
    if not isinstance(file_list, list):
        return False, "file_list 必须是数组"
    for item in file_list:
        if not isinstance(item, dict):
            return False, "file_list 元素必须是对象"
        file_url = item.get("file_url")
        if not file_url and not item.get("file_base64"):
            return False, "file_list 元素必须包含 file_url 或 file_base64"
        # file_url 必须是可访问的 http/https 链接；本地路径（如 C:\xxx、/Users/xxx）
        # 服务端无法下载，须改用 file_base64 直传
        if file_url and not (
            isinstance(file_url, str)
            and file_url.strip().lower().startswith(("http://", "https://"))
        ):
            return False, (
                "file_url 必须是 http/https 可访问链接；"
                "检测到本地文件路径，服务端无法下载，"
                "请读取该文件后改用 file_base64 直传"
            )
        if item.get("file_type") and item["file_type"] not in ("pic",):
            return False, "file_list 仅接受图片（pic）；PDF 请由 AI 提取文字后拼入 query"
    return True, ""


# ── 后置标记（stderr，供上层转为固定话术）───────────────
# 两个标记都不是错误，退出码仍为 0，不得原样展示给用户。

AUTH_NOTICE_PREFIX = "[WY_AUTH]"          # 首次自动注册成功，仅一次
UPDATE_NOTICE_PREFIX = "[WY_UPDATE]"      # 检测到新版本
UPDATE_CHECK_TIMEOUT_SECONDS = 5


def emit_update_notice() -> None:
    """查询成功后执行版本检查：有更新时向 stderr 输出一行标记。

    - 后置执行：主回答已输出并 flush，不阻塞、不污染 markdown_content；
    - 失败静默：任何异常都不影响本次回答，也不改变退出码；
    - 节流与去重由 version_check 内部负责
    """
    try:
        version_check = importlib.import_module("version_check")
        result = version_check.check(timeout=UPDATE_CHECK_TIMEOUT_SECONDS)
        if result.get("status") == "update_available" and result.get("remote"):
            print(
                f"{UPDATE_NOTICE_PREFIX} UPDATE_AVAILABLE "
                f"local={result['local']} remote={result['remote']}",
                file=sys.stderr,
            )
    except Exception:
        pass


# ── 主流程 ────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    user_query: str = args["query"]
    file_list = args["file_list"]
    region: str = args["region"]
    no_followup: bool = args["no_followup"]

    # stdin 模式
    if args["use_stdin"]:
        stdin_raw = sys.stdin.read()
        if not stdin_raw.strip():
            print("错误: --stdin 模式需要管道输入 JSON 数据", file=sys.stderr)
            print('示例: echo \'{"query":"..."}\' | python3 query.py --stdin', file=sys.stderr)
            sys.exit(1)

        try:
            stdin_data = json.loads(stdin_raw)
        except json.JSONDecodeError as e:
            print(f"错误: stdin JSON 解析失败 - {e}", file=sys.stderr)
            sys.exit(1)

        query_val = stdin_data.get("query")
        if not isinstance(query_val, str) or not query_val.strip():
            print("错误: stdin JSON 必须包含非空 query 字段", file=sys.stderr)
            sys.exit(1)

        user_query = query_val.strip()

        if "file_list" in stdin_data:
            valid, error = validate_file_list(stdin_data["file_list"])
            if not valid:
                print(f"错误: {error}", file=sys.stderr)
                sys.exit(1)
            file_list = stdin_data["file_list"]

        region_val = stdin_data.get("region")
        if isinstance(region_val, str) and region_val.strip():
            region = region_val.strip()

        # stdin 中也可指定 no_followup（报告解读场景必传）
        if stdin_data.get("no_followup"):
            no_followup = True

    # 读取 API Key：本地已存直接用；缺失时自动兑换注册（不打断查询）
    cred = auth.ensure_api_key()
    api_key = cred.get("key")
    # 本次是否触发首次注册：成功后输出一次性告知标记
    registered = bool(cred.get("registered"))
    if not api_key:
        print(
            f"自动注册失败：{cred.get('message', '未知错误')}，请稍后重试。",
            file=sys.stderr,
        )
        sys.exit(1)

    if not user_query:
        print(
            "缺少查询内容。用法：\n"
            '  python3 query.py "我想咨询皮肤科医生"\n'
            '  或 echo \'{"query":"..."}\' | python3 query.py --stdin',
            file=sys.stderr,
        )
        sys.exit(1)

    # 如果有用户地区信息，附加到查询中以便 API 精准匹配
    if region:
        user_query = f"用户所在地区：{region}。{user_query}"

    # 报告解读场景：跳过追问，直接解读
    # 在 query 末尾追加「直接解读」关键词，触发服务端跳过追问机制
    if no_followup:
        user_query = f"{user_query}（请直接解读报告，无需追问，直接给出解读结果）"

    # 构建请求体
    body: dict[str, Any] = {"query": user_query}
    if isinstance(file_list, list) and len(file_list) > 0:
        body["file_list"] = file_list

    body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")

    # 发送请求（凭证失效时强制重新兑换并重试一次）
    def _send(key: str) -> dict[str, Any]:
        req = urllib.request.Request(
            API_URL,
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                print(f"请求失败: HTTP {response.status}", file=sys.stderr)
                sys.exit(1)
            return json.loads(response.read().decode("utf-8"))

    try:
        data = _send(api_key)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            recred = auth.ensure_api_key(force=True)
            new_key = recred.get("key")
            if new_key and new_key != api_key:
                api_key = new_key
                try:
                    data = _send(api_key)
                except urllib.error.HTTPError as e2:
                    print(f"请求失败: HTTP {e2.code}", file=sys.stderr)
                    sys.exit(1)
                except (TimeoutError, urllib.error.URLError, ValueError):
                    print("重试请求异常，请稍后重试。", file=sys.stderr)
                    sys.exit(1)
            else:
                print("API Key 已失效且自动更换失败，请稍后重试。", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"请求失败: HTTP {e.code}", file=sys.stderr)
            sys.exit(1)
    except TimeoutError:
        print("请求超时（已等待 2 分钟），请稍后重试。", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        reason = str(e.reason)
        if "timed out" in reason:
            print("请求超时（已等待 2 分钟），请稍后重试。", file=sys.stderr)
        else:
            print(f"请求异常: {reason}", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        # 200 但响应非 JSON（如网关/CDN 错误页），避免堆栈裸崩
        # json.JSONDecodeError 与 UnicodeDecodeError 均为 ValueError 子类
        print("服务暂时不可用（响应格式异常），请稍后重试。", file=sys.stderr)
        sys.exit(1)

    # 提取 data.markdown_content 展示给用户
    content = data.get("data", {}).get("markdown_content") if isinstance(data, dict) else None
    if isinstance(content, str) and content:
        print(content)
        sys.stdout.flush()
        # 首次注册告知标记（仅一次）
        if registered:
            print(f"{AUTH_NOTICE_PREFIX} REGISTERED", file=sys.stderr)
        # 内置版本检查：后置执行，失败静默，不影响本次回答
        emit_update_notice()
    else:
        print("未获取到有效回复内容", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
