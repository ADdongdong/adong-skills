#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
识别 PDF 内容并输出结果

职责：
    1. 定位并获取 PDF 二进制内容（FileService.get_blob + 磁盘缓存）
    2. 标准型 PDF 用 pdfplumber 提取表格
    3. 图片型/扫描件或 pdfplumber 失败时，调用 OCR 接口，直接返回原始识别文本
    4. 多个 PDF 时合并为一份结果打印并返回，供 LLM 整理后调用 json_to_excel

依赖库：pip install pdfplumber requests
"""

import io
import json
import logging
import os
import hashlib
import re
import socket
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None

# 安全加固（安装时由用户确认后修改）：
# 原默认值为公网明文接口 http://82.156.129.26:8330/pdf/content/extract，
# 图片型/扫描件 PDF 会把含账号、户名、金额的流水原件明文外发，存在数据泄露风险。
# 现改为本地占位地址：默认不外发，未自建识别服务时 OCR 分支必然失败并明确提示。
# 如需启用远程 OCR，请显式设置环境变量 PDF_EXTRACT_API_URL 指向可信服务（建议 https）。
DEFAULT_API_URL = "http://127.0.0.1:8330/pdf/content/extract"
API_URL = os.environ.get("PDF_EXTRACT_API_URL", DEFAULT_API_URL)


def _env_int(name: str, default: int) -> int:
    try:
        v = os.environ.get(name)
        return int(v) if v else default
    except (TypeError, ValueError):
        return default


CONNECT_TIMEOUT = _env_int("PDF_EXTRACT_CONNECT_TIMEOUT", 30)
READ_TIMEOUT = _env_int("PDF_EXTRACT_READ_TIMEOUT", 120)
MAX_RETRIES = _env_int("PDF_EXTRACT_MAX_RETRIES", 2)
RETRY_BACKOFF = 2
TEXT_PAGE_THRESHOLD = 5


class ApiError(Exception):
    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


_CACHE_DIR = os.path.join(tempfile.gettempdir(), "forp_bank_statement_check_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)


def _cache_key(file_id: str) -> str:
    return hashlib.md5(file_id.encode()).hexdigest()


def _load_bytes_cache(file_id: str) -> Optional[bytes]:
    path = os.path.join(_CACHE_DIR, f"{_cache_key(file_id)}.bin")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception as e:  # noqa: BLE001
        logger.warning("[bank_statement_check] 读字节缓存失败: %s", e)
        return None


def _check_deps() -> List[str]:
    missing = []
    if pdfplumber is None:
        missing.append("pdfplumber")
    if requests is None:
        missing.append("requests")
    return missing


def _get_file_name(f: Dict[str, Any]) -> str:
    return f.get("name", "") or f.get("filename", "") or f.get("original_name", "")


def _is_pdf(f: Dict[str, Any]) -> bool:
    name = _get_file_name(f).lower()
    ext = (f.get("extension") or "").lower().lstrip(".")
    ftype = (f.get("type") or "").lower()
    return name.endswith(".pdf") or ext == "pdf" or "pdf" in ftype


def _normalize_file_ids(raw: Any) -> List[str]:
    """将 file_ids 规范为去重后的 ID 列表，支持数组、逗号分隔字符串、单个 ID。"""
    if not raw:
        return []
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.replace("，", ",").split(",") if p.strip()]
        return list(dict.fromkeys(parts))
    if isinstance(raw, (list, tuple)):
        ids: List[str] = []
        for item in raw:
            ids.extend(_normalize_file_ids(item))
        return list(dict.fromkeys(ids))
    return [str(raw).strip()] if str(raw).strip() else []


def _locate_pdfs(files: List[Dict], file_ids: Optional[List[str]]) -> List[Dict]:
    if not files:
        return []
    if file_ids:
        result = []
        for fid in file_ids:
            matched = None
            for f in files:
                if f.get("id") == fid:
                    matched = f
                    break
            if matched:
                result.append(matched)
            else:
                logger.warning("[bank_statement_check] 未在附件中找到 file_id=%s", fid)
        return result
    return [f for f in files if _is_pdf(f)]


def _get_file_bytes(file_id: str, file_info: Dict, context: Dict) -> Optional[bytes]:
    cached_bytes = _load_bytes_cache(file_id)
    if cached_bytes:
        logger.info("缓存命中文件内容: %s", file_id)
        return cached_bytes

    file_location = file_info.get("id", "") or file_id
    user_id = (
        file_info.get("created_by")
        or context.get("user_id", "")
        or (context.get("extra") or {}).get("user_id", "")
    )

    try:
        from api.db.services.file_service import FileService
        if file_location and user_id:
            content = FileService.get_blob(user_id, file_location)
            if content:
                if isinstance(content, bytes):
                    return content
                if isinstance(content, str):
                    return content.encode("utf-8")
                return bytes(content)
    except Exception as e:  # noqa: BLE001
        logger.warning("[bank_statement_check] FileService.get_blob 失败: %s", e)

    url = file_info.get("url", "")
    if url and requests is not None:
        try:
            extra = context.get("extra") or {}
            token = context.get("token") or extra.get("token") or extra.get("access_token") or ""
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            resp = requests.get(url, headers=headers, timeout=120)
            if resp.status_code == 200 and resp.content:
                return resp.content
        except Exception as e:  # noqa: BLE001
            logger.warning("[bank_statement_check] url 下载异常: %s", e)

    local_path = file_info.get("path") or file_info.get("local_path") or ""
    if local_path and os.path.isfile(local_path):
        try:
            with open(local_path, "rb") as fp:
                return fp.read()
        except Exception as e:  # noqa: BLE001
            logger.warning("[bank_statement_check] 读取本地文件失败: %s", e)

    return None


def _count_rows(page_tables: List[Dict]) -> int:
    total = 0
    for page_info in page_tables:
        for table in page_info.get("tables", []):
            for row in table:
                if any(str(c).strip() for c in row):
                    total += 1
    return total


def _is_image_pdf(pdf_bytes: bytes) -> bool:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            if not pdf.pages:
                return True
            low_text_pages = 0
            for page in pdf.pages:
                text = (page.extract_text() or "").strip()
                if len(text) < TEXT_PAGE_THRESHOLD:
                    low_text_pages += 1
            return low_text_pages >= len(pdf.pages) / 2
    except Exception as e:  # noqa: BLE001
        logger.warning("[bank_statement_check] 判断 PDF 类型失败，按图片型处理: %s", e)
        return True


def _extract_tables_pdfplumber(pdf_bytes: bytes) -> List[Dict]:
    result = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if tables:
                cleaned = []
                for table in tables:
                    rows = [[str(c).strip() if c is not None else "" for c in row] for row in table]
                    if any(any(cell for cell in row) for row in rows):
                        cleaned.append(rows)
                if cleaned:
                    result.append({"page": idx, "tables": cleaned})
    return result


# ---------------------------------------------------------------------------
# 无横线版式兜底：真实银行流水很多没有表格网格线，默认 lines 策略提取不到。
# 用词坐标聚类重建表格：①按 top 聚行 ②定位表头行（含>=3个列名别名）
# ③表头词按 x 重叠聚成列并命名（可处理"交易时间"跨两行换行）
# ④数据行词按中心点落入相邻列中心中点区间归列。
# ---------------------------------------------------------------------------
_COL_ALIASES = (
    "交易日期", "交易日", "记账日期", "发生日期", "入账日期", "日期",
    "交易时间", "记账时间", "发生时间", "交易时刻", "入账时间",
    "摘要", "用途", "备注", "说明", "交易摘要", "附言",
    "交易金额", "发生额", "借方金额", "贷方金额", "收入", "支出", "金额",
    "对方账号", "对方账户", "对手账号", "收款账号", "付款账号", "对方卡号",
    "对方户名", "对方名称", "对手户名", "收款人", "付款人", "对方姓名", "对手方",
    "当前账户", "本方账号", "卡号", "账户号码", "银行账号",
    "当前户名", "本方户名", "账户名称", "本方名称",
    "账户余额", "余额", "银行", "开户行", "交易类型", "借贷标志",
)
_DATE_RE = re.compile(r"\d{4}[-/年.]\d{1,2}|\d{8}")


def _cluster_lines(words: List[Dict], y_tol: float = 4.0) -> List[List[Dict]]:
    lines: List[List[Dict]] = []
    for w in sorted(words, key=lambda x: (x["top"], x["x0"])):
        if lines and abs(w["top"] - lines[-1][0]["top"]) <= y_tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    for ln in lines:
        ln.sort(key=lambda x: x["x0"])
    return lines


def _header_hit_count(line: List[Dict]) -> int:
    text = "".join(w["text"] for w in line)
    return sum(1 for a in _COL_ALIASES if a in text)


def _build_columns(header_words: List[Dict]) -> List[Dict]:
    """把表头词按 x 区间重叠聚类成列；返回 [{label, center}] 按 x 排序。"""
    clusters: List[List[Dict]] = []
    for w in sorted(header_words, key=lambda x: x["x0"]):
        placed = False
        for c in clusters:
            lo, hi = min(x["x0"] for x in c), max(x["x1"] for x in c)
            if w["x0"] < hi + 6 and w["x1"] > lo - 6:  # x 区间重叠或间隙很小
                c.append(w)
                placed = True
                break
        if not placed:
            clusters.append([w])
    cols = []
    for c in clusters:
        label = "".join(x["text"] for x in sorted(c, key=lambda x: (round(x["top"] / 4), x["x0"])))
        center = sum((x["x0"] + x["x1"]) / 2 for x in c) / len(c)
        cols.append({"label": label, "center": center})
    cols.sort(key=lambda x: x["center"])
    return cols


def _assign_word_to_column(word: Dict, centers: List[float]) -> int:
    c = (word["x0"] + word["x1"]) / 2
    best, best_gap = 0, float("inf")
    for i, ctr in enumerate(centers):
        gap = abs(c - ctr)
        if gap < best_gap:
            best, best_gap = i, gap
    return best


def _extract_tables_by_words(pdf_bytes: bytes) -> List[Dict]:
    result: List[Dict] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            try:
                words = page.extract_words(x_tolerance=1.5, y_tolerance=3)
            except Exception:  # noqa: BLE001
                continue
            if not words:
                continue
            lines = _cluster_lines(words)
            header_idx = next(
                (i for i, ln in enumerate(lines) if _header_hit_count(ln) >= 3), None
            )
            if header_idx is None:
                continue
            # 数据行 = 表头之后、以日期开头（或含日期且含金额）的行
            data_rows: List[List[Dict]] = []
            cur_cols: List[Dict] = []
            for ln in lines[header_idx + 1:]:
                text = "".join(w["text"] for w in ln)
                if _DATE_RE.search(text):
                    data_rows.append(ln)
                elif data_rows:
                    # 表格之后的内容（合计/脚注/印章），停止收集
                    break
                elif not cur_cols and _header_hit_count(ln) >= 2:
                    cur_cols.extend(ln)  # 表头跨行换行的第二段
            header_words = list(lines[header_idx]) + cur_cols
            cols = _build_columns(header_words)
            if len(cols) < 3 or not data_rows:
                continue
            centers = [c["center"] for c in cols]
            ncol = len(centers)
            rows: List[List[str]] = [[c["label"] for c in cols]]
            for ln in data_rows:
                row = [""] * ncol
                for w in ln:
                    j = _assign_word_to_column(w, centers)
                    row[j] = (row[j] + w["text"]).strip()
                if any(row):
                    rows.append(row)
            if len(rows) > 1:
                result.append({"page": idx, "tables": [rows], "method": "words"})
    return result


def _parse_host_port(url: str) -> tuple:
    try:
        rest = url.split("//", 1)[1].split("/", 1)[0]
        if ":" in rest:
            h, p = rest.rsplit(":", 1)
            return h, int(p)
        return rest, 80
    except Exception:
        return "", 0


def _describe_network_error(exc: Exception) -> str:
    raw = str(exc)
    if requests is not None and isinstance(exc, requests.Timeout):
        return f"请求超时(连接 {CONNECT_TIMEOUT}s / 读取 {READ_TIMEOUT}s,目标 {_parse_host_port(API_URL)[0]})"
    if requests is not None and isinstance(exc, requests.exceptions.ProxyError):
        return "系统代理拦截或拒绝(已重设直连仍失败)"
    if requests is not None and isinstance(exc, requests.ConnectionError):
        return f"连接失败:{raw or '连接被拒绝或地址不可达'}"
    return raw


def call_extract_api(pdf_bytes: bytes, file_name: str = "document.pdf") -> Dict[str, Any]:
    if requests is None:
        raise ApiError("missing_requests", "OCR 接口依赖缺失：requests")

    _host, _port = _parse_host_port(API_URL)

    # 安全告警：非本机地址意味着 PDF 原始内容将外发到远端服务
    if _host and _host not in ("127.0.0.1", "localhost", "::1"):
        logger.warning(
            "[安全告警] 当前 PDF 识别接口为远端地址 %s，"
            "调用后本文件的完整内容（可能含银行账号、户名、金额等敏感信息）将被上传至该服务器。",
            API_URL,
        )

    if _host and _port:
        try:
            _probe = socket.create_connection((_host, _port), timeout=8)
            _probe.close()
            logger.info("[OCR接口] TCP 探活 %s:%s OK", _host, _port)
        except (socket.timeout, TimeoutError):
            raise ApiError("tcp_unreachable", f"TCP 不可达:{_host}:{_port} 8 秒内未收到 SYN/ACK")
        except Exception as exc:
            raise ApiError("tcp_unreachable", f"TCP 不可达:{_host}:{_port} -> {exc}")

    no_proxy = {"http": None, "https": None}
    last_err = ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            files = {"pdf_stream": (file_name, pdf_bytes, "application/pdf")}
            timeout = (CONNECT_TIMEOUT, READ_TIMEOUT)
            logger.info(
                "[OCR接口] 第 %s/%s 次调用: %s, 文件大小=%s bytes",
                attempt, MAX_RETRIES, API_URL, len(pdf_bytes),
            )
            resp = requests.post(API_URL, files=files, timeout=timeout, proxies=no_proxy)
            if resp.status_code >= 500:
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                raise requests.RequestException(last_err)
            if resp.status_code != 200:
                raise ApiError(
                    "api_http_error",
                    f"识别接口返回 HTTP {resp.status_code}: {resp.text[:200]}",
                )

            body = resp.json()
            code = body.get("code")
            message = body.get("message", "")
            data = body.get("data")

            if code == 200:
                if data is None or data == "":
                    raise ApiError("api_empty_result", f"识别接口返回空数据(code=200): {message}")
                return data

            raise ApiError("api_error", f"识别接口返回错误(code={code}): {message}")

        except ApiError:
            raise
        except (requests.ConnectionError, requests.Timeout, requests.RequestException) as exc:
            last_err = _describe_network_error(exc)
            logger.warning("[OCR接口] 网络异常(第 %s 次): %s", attempt, last_err)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF ** (attempt - 1))

    raise ApiError(
        "network_failed",
        f"无法连接 PDF 识别接口(已重试 {MAX_RETRIES} 次): {last_err}。"
        f"请确认平台所在机器可访问 {API_URL}",
    )


def _normalize_api_pages(out: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = None
    for key in ("pages", "items", "page_list", "results"):
        if isinstance(out.get(key), list):
            raw = out[key]
            break
    if raw is None and isinstance(out.get("data"), dict):
        inner = out["data"]
        for key in ("pages", "items", "page_list", "results"):
            if isinstance(inner.get(key), list):
                raw = inner[key]
                break

    pages: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw or [], 1):
        if not isinstance(item, dict):
            pages.append({"page": idx, "source": "", "content": str(item)})
            continue
        page_no = item.get("page") or item.get("page_no") or item.get("页码") or idx
        try:
            page_no = int(page_no)
        except (TypeError, ValueError):
            page_no = idx
        content = item.get("content")
        if content is None:
            content = item.get("text") or item.get("内容") or ""
        source = (item.get("source") or item.get("type") or "").lower()
        pages.append({
            "page": page_no,
            "source": source if source in ("text", "ocr", "empty") else "",
            "content": str(content),
        })
    return pages


def _normalize_api_stats(out: Dict[str, Any], pages: List[Dict[str, Any]]) -> Dict[str, int]:
    stats = out.get("stats") if isinstance(out.get("stats"), dict) else {}
    text_pages = stats.get("text_pages")
    ocr_pages = stats.get("ocr_pages")
    empty_pages = stats.get("empty_pages")
    if text_pages is None or ocr_pages is None or empty_pages is None:
        text_pages = sum(1 for p in pages if p["source"] == "text")
        ocr_pages = sum(1 for p in pages if p["source"] == "ocr")
        empty_pages = sum(1 for p in pages if p["source"] == "empty" or not p["content"].strip())
    return {
        "text_pages": int(text_pages),
        "ocr_pages": int(ocr_pages),
        "empty_pages": int(empty_pages),
    }


def _extract_content_via_api(pdf_bytes: bytes, file_name: str = "document.pdf") -> Dict[str, Any]:
    """调用 OCR 接口，直接返回原始识别结果（不做表格解析）。"""
    out = call_extract_api(pdf_bytes, file_name=file_name)
    if not isinstance(out, dict):
        raise ApiError("api_bad_format", f"识别接口返回了意外的数据格式: {type(out).__name__}")

    pages = _normalize_api_pages(out)
    stats = _normalize_api_stats(out, pages)
    total_pages = out.get("total_pages") or out.get("总页数") or len(pages)
    try:
        total_pages = int(total_pages)
    except (TypeError, ValueError):
        total_pages = len(pages)

    full_text = "\n\n".join(
        f"----- 第 {p['page']} 页{'[OCR]' if p['source'] == 'ocr' else ''} -----\n{p['content'] or '(本页无内容)'}"
        for p in pages
    )

    return {
        "result_type": "text",
        "total_pages": total_pages,
        "extracted_count": len(pages),
        "text_pages": stats["text_pages"],
        "ocr_pages": stats["ocr_pages"],
        "empty_pages": stats["empty_pages"],
        "pages": pages,
        "text": full_text,
    }


def _extract_content_pdfplumber(pdf_bytes: bytes) -> Dict[str, Any]:
    tables_data = _extract_tables_pdfplumber(pdf_bytes)
    return {
        "result_type": "tables",
        "total_pages": len(tables_data),
        "extracted_count": len(tables_data),
        "table_count": sum(len(p.get("tables", [])) for p in tables_data),
        "row_count": _count_rows(tables_data),
        "pages": tables_data,
    }


def _extract_pdf_content(pdf_bytes: bytes, file_name: str = "document.pdf") -> Tuple[Dict[str, Any], bool, str]:
    if _is_image_pdf(pdf_bytes):
        logger.info("检测为图片型 PDF，直接使用 OCR 接口")
        return _extract_content_via_api(pdf_bytes, file_name=file_name), True, "ocr_api"

    tables_result = _extract_content_pdfplumber(pdf_bytes)
    if tables_result["pages"]:
        logger.info("pdfplumber 提取成功，共 %s 页", tables_result["total_pages"])
        return tables_result, False, "pdfplumber"

    # 无横线版式兜底：lines 策略提不到表格时，先用词坐标重建，避免不必要地外发 OCR
    words_result = _extract_tables_by_words(pdf_bytes)
    if words_result:
        logger.info("pdfplumber lines 策略无表格，词坐标重建成功（无横线版式）")
        return {
            "result_type": "tables",
            "total_pages": len(words_result),
            "extracted_count": len(words_result),
            "table_count": sum(len(p.get("tables", [])) for p in words_result),
            "row_count": _count_rows(words_result),
            "pages": words_result,
        }, False, "pdfplumber_words"

    logger.info("pdfplumber 未提取到表格，降级 OCR 接口")
    return _extract_content_via_api(pdf_bytes, file_name=file_name), True, "ocr_api"


def _has_content(result: Dict[str, Any]) -> bool:
    if result.get("result_type") == "tables":
        return bool(result.get("pages"))
    if result.get("result_type") == "text":
        pages = result.get("pages") or []
        return any(str(p.get("content", "")).strip() for p in pages)
    return False


def _merge_file_results(success_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """将多个 PDF 的识别结果合并为一份。"""
    source_files = [item["file_name"] for item in success_items]
    text_parts: List[str] = []
    merged_text_pages: List[Dict[str, Any]] = []
    merged_table_pages: List[Dict[str, Any]] = []
    text_pages = ocr_pages = empty_pages = 0
    table_count = row_count = 0

    for item in success_items:
        fname = item["file_name"]
        result = json.loads(item["result_json"])
        rtype = result.get("result_type")

        if rtype == "text":
            text_pages += result.get("text_pages", 0)
            ocr_pages += result.get("ocr_pages", 0)
            empty_pages += result.get("empty_pages", 0)
            for page in result.get("pages", []):
                merged_text_pages.append({
                    "source_file": fname,
                    "page": page.get("page"),
                    "source": page.get("source", ""),
                    "content": page.get("content", ""),
                })
            text_parts.append(f"===== 文件：{fname} =====\n{result.get('text', '')}")

        elif rtype == "tables":
            table_count += result.get("table_count", 0)
            row_count += result.get("row_count", 0)
            for page in result.get("pages", []):
                merged_table_pages.append({
                    "source_file": fname,
                    "page": page.get("page"),
                    "tables": page.get("tables", []),
                })
            text_parts.append(f"===== 文件：{fname}（表格数据）=====\n{json.dumps(result.get('pages', []), ensure_ascii=False)}")

    merged: Dict[str, Any] = {
        "result_type": "merged",
        "source_count": len(source_files),
        "source_files": source_files,
        "text": "\n\n".join(text_parts),
    }
    if merged_text_pages:
        merged["pages"] = merged_text_pages
        merged["text_pages"] = text_pages
        merged["ocr_pages"] = ocr_pages
        merged["empty_pages"] = empty_pages
    if merged_table_pages:
        merged["table_pages"] = merged_table_pages
        merged["table_count"] = table_count
        merged["row_count"] = row_count
    return merged


def _build_file_result(
    fid: str,
    fname: str,
    result: Dict[str, Any],
    ocr_used: bool,
    extract_method: str,
) -> Dict[str, Any]:
    result_json = json.dumps(result, ensure_ascii=False, indent=2)

    item: Dict[str, Any] = {
        "file_id": fid,
        "file_name": fname,
        "extract_method": extract_method,
        "ocr_used": ocr_used,
        "result_type": result.get("result_type"),
        "total_pages": result.get("total_pages", 0),
        "extracted_count": result.get("extracted_count", 0),
        "result_json": result_json,
    }

    if result.get("result_type") == "tables":
        item["table_count"] = result.get("table_count", 0)
        item["row_count"] = result.get("row_count", 0)
    else:
        item["text_pages"] = result.get("text_pages", 0)
        item["ocr_pages"] = result.get("ocr_pages", 0)
        item["empty_pages"] = result.get("empty_pages", 0)
        item["text"] = result.get("text", "")

    return item


def main(input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """批量识别 PDF 内容并返回/打印识别结果。"""
    missing = _check_deps()
    if missing:
        msg = f"服务端缺少依赖库：{', '.join(missing)}，请管理员执行 pip install {' '.join(missing)}"
        logger.error(msg)
        return {"success": False, "message": msg}

    file_id = input_data.get("file_id", "") or ""
    file_ids = _normalize_file_ids(input_data.get("file_ids"))
    if file_id and not file_ids:
        file_ids = [file_id.strip()]

    files = context.get("files", []) or []
    targets = _locate_pdfs(files, file_ids if file_ids else None)
    if not targets:
        pdf_names = [_get_file_name(f) for f in files if _is_pdf(f)]
        if file_ids and not pdf_names:
            msg = f"未找到指定的 PDF 文件（file_ids={file_ids}），请确认附件已上传"
        elif not files:
            msg = "未找到要识别的 PDF 文件，请上传 PDF 附件后再试"
        else:
            msg = "未找到要识别的 PDF 文件，请上传 PDF 附件后再试"
        return {
            "success": False,
            "message": msg,
        }

    total = len(targets)
    success_items: List[Dict[str, Any]] = []
    failed_files: List[Dict[str, Any]] = []

    for idx, target in enumerate(targets, start=1):
        fid = target.get("id", "") or ""
        fname = _get_file_name(target) or "document.pdf"
        try:
            pdf_bytes = _get_file_bytes(fid, target, context)
            if not pdf_bytes:
                failed_files.append({"file_name": fname, "error": "PDF 读取失败"})
                continue

            result, ocr_used, extract_method = _extract_pdf_content(pdf_bytes, file_name=fname)
            if not _has_content(result):
                failed_files.append({"file_name": fname, "error": "未识别到有效内容"})
                continue

            success_items.append(_build_file_result(fid, fname, result, ocr_used, extract_method))
        except Exception as e:  # noqa: BLE001
            logger.error("识别 PDF %s 失败: %s", fname, e, exc_info=True)
            failed_files.append({"file_name": fname, "error": str(e)})

    success_count = len(success_items)
    failed_count = len(failed_files)

    if success_count == 0:
        return {
            "success": False,
            "message": f"{total} 个 PDF 均识别失败",
            "data": {"total": total, "success_count": 0, "failed_count": failed_count, "failed_files": failed_files},
        }

    # 单个或多个 PDF 均合并为一份结果返回
    if success_count == 1:
        single = success_items[0]
        merged_result = json.loads(single["result_json"])
        merged_result["source_count"] = 1
        merged_result["source_files"] = [single["file_name"]]
        if merged_result.get("result_type") == "text":
            merged_result["result_type"] = "merged"
    else:
        merged_result = _merge_file_results(success_items)

    result_json = json.dumps(merged_result, ensure_ascii=False, indent=2)
    print("\n===== 合并识别结果 =====")
    print(result_json)
    print("===== 合并识别结果结束 =====\n")

    msg = (
        f"已识别 {success_count}/{total} 个 PDF 并合并结果。"
        "【中间步骤·任务未完成】禁止 action=finish，禁止向用户输出进度/JSON。"
        "请静默将 data.result_json 整理为标准9列 headers+rows，"
        "立即调用 json_to_excel，并把整理结果仅放入 input.tables_json"
        "（严禁写入 thought/result，否则 ReAct JSON 解析失败）。"
    )
    if failed_count:
        msg += f"（另有 {failed_count} 个失败）"

    data: Dict[str, Any] = {
        "total": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "source_files": merged_result.get("source_files", []),
        "merged_result": merged_result,
        "result_json": result_json,
        "text": merged_result.get("text", ""),
        "next_action": "json_to_excel",
        "forbid_finish": True,
    }
    if failed_files:
        data["failed_files"] = failed_files

    logger.info("识别完成, %s/%s 个 PDF，已合并返回", success_count, total)
    return {
        "success": True,
        "message": msg,
        "data": data,
    }


def run_local_test(pdf_path: str, output_json: Optional[str] = None) -> Dict[str, Any]:
    missing = _check_deps()
    if missing:
        raise RuntimeError(f"缺少依赖库：{', '.join(missing)}，请执行 pip install {' '.join(missing)}")

    pdf_path = os.path.abspath(pdf_path)
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    file_name = os.path.basename(pdf_path)
    with open(pdf_path, "rb") as fh:
        pdf_bytes = fh.read()
    if not pdf_bytes:
        raise ValueError(f"PDF 文件为空: {pdf_path}")

    t0 = time.time()
    result, ocr_used, extract_method = _extract_pdf_content(pdf_bytes, file_name=file_name)
    elapsed = round(time.time() - t0, 1)

    if not _has_content(result):
        return {
            "success": False,
            "file_name": file_name,
            "pdf_path": pdf_path,
            "error": "未识别到有效内容",
            "elapsed_seconds": elapsed,
        }

    result_json = json.dumps(result, ensure_ascii=False, indent=2)
    print("\n===== 识别结果 =====")
    print(result_json)
    print("===== 识别结果结束 =====\n")
    out_path = output_json or os.path.splitext(pdf_path)[0] + ".result.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(result_json)

    return {
        "success": True,
        "file_name": file_name,
        "pdf_path": pdf_path,
        "output_json": out_path,
        "ocr_used": ocr_used,
        "extract_method": extract_method,
        "elapsed_seconds": elapsed,
        "result_json": result_json,
    }


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if len(sys.argv) < 2:
        print("用法: python file_to_json.py <pdf路径1> [pdf路径2 ...]")
        print("示例: python file_to_json.py ./a.pdf ./b.pdf")
        sys.exit(1)

    pdf_paths = sys.argv[1:]
    batch_results = []
    success_count = 0

    for idx, pdf_path in enumerate(pdf_paths, start=1):
        try:
            result = run_local_test(pdf_path)
        except Exception as exc:
            result = {"success": False, "file_name": os.path.basename(pdf_path), "error": str(exc)}
        batch_results.append(result)
        if result.get("success"):
            success_count += 1
            print(f"[{idx}/{len(pdf_paths)}] {result['file_name']} — 成功")
        else:
            print(f"[{idx}/{len(pdf_paths)}] {result.get('file_name', pdf_path)} — 失败：{result.get('error', '未知错误')}")

    print(f"\n批量本地测试完成：{success_count}/{len(pdf_paths)} 成功")
    sys.exit(0 if success_count > 0 else 1)
