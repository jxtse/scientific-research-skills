#!/usr/bin/env python3
"""
批量为缺失全文 PDF 的 Elsevier 文献补下结构化全文 XML。

用法:
    uv run --with pandas --with openpyxl --with pypdf python3 redownload_elsevier.py \
        --excel papers.xlsx [--check-only] [--redownload] [--limit N]

流程:
    1. 从指定 Excel 文件提取所有 Elsevier DOI (10.1016 等前缀)
    2. 检查 pdfs/ 下是否已有可用全文 PDF
    3. 对缺失 PDF 或仅有摘要页 PDF 的文献下载对应的 Elsevier XML 全文
    4. 统计报告
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from auto_paper_download.clients import (
    ElsevierClient,
    DownloadError,
    _safe_identifier,
    _article_destination,
)
from auto_paper_download.downloader import load_env_file, ELSEVIER_PREFIXES

LOGGER = logging.getLogger("redownload_elsevier")

# 摘要页判定阈值
ABSTRACT_ONLY_MAX_PAGES = 1       # 页数 ≤ 1 认为只有摘要页
ABSTRACT_ONLY_MAX_SIZE_KB = 100   # 文件 < 100KB 认为只有摘要页


def extract_elsevier_dois(excel_path: Path) -> list[str]:
    """从 Excel 文件提取所有 Elsevier DOI。"""
    df = pd.read_excel(excel_path)
    doi_col = None
    for col in df.columns:
        if col.upper() == "DOI":
            doi_col = col
            break
    if doi_col is None:
        raise ValueError(f"未找到 DOI 列，可用列: {list(df.columns)}")

    dois = []
    seen = set()
    for val in df[doi_col].dropna():
        doi = str(val).strip()
        if doi.startswith(("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/")):
            doi = doi.split("doi.org/")[-1]
        if any(doi.lower().startswith(p) for p in ELSEVIER_PREFIXES) and doi not in seen:
            seen.add(doi)
            dois.append(doi)
    return dois


def get_pdf_path(pdf_dir: Path, doi: str) -> Path:
    """根据 DOI 计算 PDF 路径。"""
    fname = _safe_identifier(doi)
    article_dir = pdf_dir / fname
    return _article_destination(article_dir, fname)


def get_xml_path(output_dir: Path, doi: str) -> Path:
    """根据 DOI 计算 XML 路径。"""
    fname = _safe_identifier(doi)
    article_dir = output_dir / fname
    article_dir.mkdir(parents=True, exist_ok=True)
    return article_dir / f"{fname}.xml"


def check_pdf_quality(pdf_path: Path) -> dict:
    """
    检测 PDF 是否为摘要页。

    返回 dict:
        exists: bool
        pages: int
        size_kb: float
        is_abstract_only: bool
        reason: str
    """
    result = {
        "exists": False,
        "pages": 0,
        "size_kb": 0.0,
        "is_abstract_only": False,
        "reason": "",
    }

    if not pdf_path.exists():
        result["reason"] = "文件不存在"
        return result

    result["exists"] = True
    result["size_kb"] = pdf_path.stat().st_size / 1024

    if result["size_kb"] < 1:
        result["is_abstract_only"] = True
        result["reason"] = "文件为空"
        return result

    try:
        reader = PdfReader(str(pdf_path))
        result["pages"] = len(reader.pages)
    except Exception as e:
        result["is_abstract_only"] = True
        result["reason"] = f"PDF 解析失败: {e}"
        return result

    if result["pages"] <= ABSTRACT_ONLY_MAX_PAGES:
        result["is_abstract_only"] = True
        result["reason"] = f"仅 {result['pages']} 页"
    elif result["size_kb"] < ABSTRACT_ONLY_MAX_SIZE_KB:
        result["is_abstract_only"] = True
        result["reason"] = f"文件过小 ({result['size_kb']:.1f} KB)"

    return result


def needs_xml_download(doi: str, pdf_dir: Path) -> tuple[bool, str]:
    """判断某篇文献是否需要补下 XML 全文。"""
    pdf_path = get_pdf_path(pdf_dir, doi)
    quality = check_pdf_quality(pdf_path)
    if not quality["exists"]:
        return True, "PDF 不存在"
    if quality["is_abstract_only"]:
        return True, quality["reason"]
    return False, ""


class StatusLog:
    """Append-only JSONL record of successful / failed Elsevier XML downloads.

    Writes two files under output_dir:
      _success.jsonl  — one JSON object per successful download
      _failures.jsonl — one JSON object per failure

    Each append is flushed + fsynced so Ctrl-C never loses a recorded line.
    """

    SUCCESS_FILE = "_success.jsonl"
    FAILURE_FILE = "_failures.jsonl"

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.success_path = output_dir / self.SUCCESS_FILE
        self.failure_path = output_dir / self.FAILURE_FILE
        self.success_dois: set[str] = set()
        self.historical_failure_count = 0
        self._load()

    def _load(self) -> None:
        if self.success_path.exists():
            with self.success_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    doi = rec.get("doi")
                    if doi:
                        self.success_dois.add(doi)
        if self.failure_path.exists():
            with self.failure_path.open("r", encoding="utf-8") as fh:
                self.historical_failure_count = sum(
                    1 for line in fh if line.strip()
                )

    def is_done(self, doi: str) -> bool:
        return doi in self.success_dois

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _append(self, path: Path, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def record_success(self, doi: str, xml_path: Path, bytes_written: int) -> None:
        try:
            rel = xml_path.relative_to(self.output_dir)
        except ValueError:
            rel = xml_path
        self._append(
            self.success_path,
            {
                "doi": doi,
                "xml": str(rel),
                "bytes": int(bytes_written),
                "ts": self._now_iso(),
            },
        )
        self.success_dois.add(doi)

    def record_failure(
        self,
        doi: str,
        reason: str,
        http_status: int | None = None,
    ) -> None:
        self._append(
            self.failure_path,
            {
                "doi": doi,
                "reason": reason,
                "http_status": http_status,
                "ts": self._now_iso(),
            },
        )


def download_one(
    doi: str,
    output_dir: Path,
    elsevier_client: ElsevierClient | None,
    overwrite: bool = False,
) -> Path | None:
    """下载单篇 Elsevier XML 全文，返回 XML 路径或 None。"""
    if not elsevier_client:
        return None

    xml_path = get_xml_path(output_dir, doi)
    if xml_path.exists() and not overwrite:
        return xml_path

    try:
        elsevier_client.download_structured_full_text(
            doi=doi,
            destination=xml_path,
            http_accept="text/xml",
            view="FULL",
            overwrite=overwrite,
        )
        return xml_path
    except DownloadError as exc:
        LOGGER.debug("Elsevier FULL XML 失败 %s: %s", doi, exc)
        if "INVALID_INPUT" not in str(exc):
            return None

    try:
        elsevier_client.download_structured_full_text(
            doi=doi,
            destination=xml_path,
            http_accept="text/xml",
            view=None,
            overwrite=overwrite,
        )
        return xml_path
    except DownloadError as exc:
        LOGGER.debug("Elsevier 默认 XML 失败 %s: %s", doi, exc)

    return None


def main():
    parser = argparse.ArgumentParser(description="为缺失全文 PDF 的 Elsevier 文献补下 XML 全文")
    parser.add_argument(
        "--excel", type=Path, required=True,
        help="输入 Excel 文件路径，需包含 DOI 列",
    )
    parser.add_argument(
        "--pdf-dir", type=Path, default=PROJECT_ROOT / "pdfs",
        help="已有 PDF 目录，用于判断哪些 Elsevier 文献缺全文 (默认: pdfs/)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=PROJECT_ROOT / "elsevier_fulltext_xml",
        help="XML 输出目录 (默认: elsevier_fulltext_xml/)",
    )
    parser.add_argument("--check-only", action="store_true", help="仅检测哪些 DOI 需要补 XML，不下载")
    parser.add_argument("--redownload", action="store_true", help="强制重下所有需要补 XML 的文献")
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument(
        "--resume", dest="resume", action="store_true", default=True,
        help="读 _success.jsonl，跳过已成功的 DOI (默认开启)",
    )
    resume_group.add_argument(
        "--no-resume", dest="resume", action="store_false",
        help="忽略 _success.jsonl (磁盘上 XML 存在仍会跳过)",
    )
    parser.add_argument(
        "--long-pause-every", type=int, default=200,
        help="每下 N 篇触发一次长休眠 (默认 200；0 = 禁用)",
    )
    parser.add_argument(
        "--long-pause-seconds", type=float, default=14400.0,
        help="长休眠时长，秒 (默认 14400 = 4 小时)",
    )
    parser.add_argument("--limit", type=int, help="限制处理的 DOI 数量（调试用）")
    parser.add_argument(
        "--delay", type=float, default=3.0,
        help="常规请求间隔秒数 (默认 3.0)",
    )
    parser.add_argument("--verbose", action="store_true", help="启用调试日志")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    # 加载环境变量
    load_env_file(PROJECT_ROOT / ".env")

    # 提取 DOI
    LOGGER.info("从 %s 提取 Elsevier DOI ...", args.excel)
    dois = extract_elsevier_dois(args.excel)
    LOGGER.info("共找到 %d 个 Elsevier DOI", len(dois))

    if args.limit:
        dois = dois[: args.limit]
        LOGGER.info("限制处理前 %d 个 DOI", args.limit)

    pdf_dir = args.pdf_dir
    output_dir = args.output_dir

    # ── 仅检测模式 ──
    if args.check_only:
        return run_check_only(dois, pdf_dir, output_dir)

    # 初始化客户端
    elsevier_client = None
    try:
        elsevier_client = ElsevierClient()
        LOGGER.info("Elsevier API 客户端已就绪")
    except ValueError as e:
        LOGGER.warning("Elsevier 客户端初始化失败: %s", e)

    if not elsevier_client:
        LOGGER.error("Elsevier 客户端不可用，退出。")
        sys.exit(1)

    status = StatusLog(output_dir)
    LOGGER.info(
        "从状态文件恢复: 已成功 %d 篇, 历史失败 %d 条",
        len(status.success_dois),
        status.historical_failure_count,
    )

    # ── 仅重下载模式 ──
    if args.redownload:
        return run_redownload(
            dois, pdf_dir, output_dir, elsevier_client,
            status=status,
            delay=args.delay,
            long_pause_every=args.long_pause_every,
            long_pause_seconds=args.long_pause_seconds,
            resume=args.resume,
        )

    # ── 完整流程：检查 PDF → 下载 XML ──
    run_full(
        dois, pdf_dir, output_dir, elsevier_client,
        status=status,
        delay=args.delay,
        long_pause_every=args.long_pause_every,
        long_pause_seconds=args.long_pause_seconds,
        resume=args.resume,
    )


def run_check_only(dois: list[str], pdf_dir: Path, output_dir: Path):
    """仅检测哪些 DOI 需要补 XML。"""
    stats = {
        "total": len(dois),
        "pdf_ok": 0,
        "needs_xml": 0,
        "xml_ready": 0,
    }
    needs_xml_list = []

    for doi in dois:
        need_xml, reason = needs_xml_download(doi, pdf_dir)
        xml_path = get_xml_path(output_dir, doi)
        if need_xml:
            stats["needs_xml"] += 1
            if xml_path.exists():
                stats["xml_ready"] += 1
            needs_xml_list.append((doi, reason, xml_path.exists()))
        else:
            stats["pdf_ok"] += 1

    print_report(stats, needs_xml_list)


def run_redownload(
    dois: list[str],
    pdf_dir: Path,
    output_dir: Path,
    elsevier_client: ElsevierClient | None,
    *,
    status: StatusLog,
    delay: float,
    long_pause_every: int,
    long_pause_seconds: float,
    resume: bool,  # accepted but intentionally unused: --redownload forces re-fetch
):
    """强制重下所有需要补 XML 的文献。"""
    target_dois = []
    for doi in dois:
        need_xml, _ = needs_xml_download(doi, pdf_dir)
        if need_xml:
            target_dois.append(doi)

    LOGGER.info("发现 %d 篇需要补 XML 的文献，开始强制重下 ...", len(target_dois))
    downloaded = 0
    failed = 0

    for i, doi in enumerate(target_dois, 1):
        LOGGER.info("[%d/%d] 重新下载 XML %s", i, len(target_dois), doi)
        try:
            result = download_one(doi, output_dir, elsevier_client, overwrite=True)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            status.record_failure(doi, f"unexpected: {exc}")
            LOGGER.warning("  下载异常: %s (%s)", doi, exc)
        else:
            if result:
                downloaded += 1
                size = result.stat().st_size if result.exists() else 0
                status.record_success(doi, result, size)
                LOGGER.info("  成功下载 XML: %s", result)
            else:
                failed += 1
                status.record_failure(doi, "download_one returned None")
                LOGGER.warning("  下载失败: %s", doi)

        is_last = i == len(target_dois)
        if is_last:
            break
        if long_pause_every > 0 and i % long_pause_every == 0:
            LOGGER.info("长休眠 %.0fs (已完成 %d 篇)", long_pause_seconds, i)
            time.sleep(long_pause_seconds)
        elif delay:
            time.sleep(delay)

    LOGGER.info("=== XML 重下载完成 ===")
    LOGGER.info("成功下载: %d", downloaded)
    LOGGER.info("下载失败: %d", failed)
    LOGGER.info("累计成功 (含历史): %d", len(status.success_dois))


def run_full(
    dois: list[str],
    pdf_dir: Path,
    output_dir: Path,
    elsevier_client: ElsevierClient | None,
    *,
    status: StatusLog,
    delay: float,
    long_pause_every: int,
    long_pause_seconds: float,
    resume: bool,
):
    """完整流程：识别缺失全文 PDF → 下载 XML。"""
    stats = {
        "total": len(dois),
        "pdf_ok": 0,
        "needs_xml": 0,
        "xml_already_present": 0,
        "xml_downloaded": 0,
        "download_failed": 0,
    }

    # ── 第一轮：识别需要补 XML 的 DOI ──
    LOGGER.info("=" * 60)
    LOGGER.info("第一轮：识别缺失全文 PDF 的 Elsevier 文献")
    LOGGER.info("=" * 60)

    target_dois: list[tuple[str, str]] = []
    for i, doi in enumerate(dois, 1):
        need_xml, reason = needs_xml_download(doi, pdf_dir)
        if need_xml:
            target_dois.append((doi, reason))
            stats["needs_xml"] += 1
            xml_path = get_xml_path(output_dir, doi)
            if xml_path.exists():
                stats["xml_already_present"] += 1
                LOGGER.info("[%d/%d] 已有 XML %s (%s)", i, len(dois), doi, reason)
        else:
            stats["pdf_ok"] += 1

    LOGGER.info("识别完成: %d 已有全文 PDF, %d 需要补 XML, %d 已有 XML",
                stats["pdf_ok"], stats["needs_xml"], stats["xml_already_present"])

    # ── 第二轮：下载缺失 XML ──
    LOGGER.info("")
    LOGGER.info("=" * 60)
    LOGGER.info("第二轮：下载缺失的 Elsevier XML 全文")
    LOGGER.info("=" * 60)

    pending = [
        (doi, reason) for doi, reason in target_dois
        if (not resume or not status.is_done(doi))
        and not get_xml_path(output_dir, doi).exists()
    ]
    for i, (doi, reason) in enumerate(pending, 1):
        LOGGER.info("[%d/%d] 下载 XML %s (%s)", i, len(pending), doi, reason)
        try:
            result = download_one(doi, output_dir, elsevier_client)
        except Exception as exc:  # noqa: BLE001 — unexpected network/runtime errors
            stats["download_failed"] += 1
            status.record_failure(doi, f"unexpected: {exc}")
            LOGGER.warning("  XML 下载异常: %s (%s)", doi, exc)
        else:
            if result:
                stats["xml_downloaded"] += 1
                size = result.stat().st_size if result.exists() else 0
                status.record_success(doi, result, size)
                LOGGER.info("  XML 已保存: %s", result)
            else:
                stats["download_failed"] += 1
                status.record_failure(doi, "download_one returned None")
                LOGGER.warning("  XML 下载失败: %s", doi)

        is_last = i == len(pending)
        if is_last:
            break
        if long_pause_every > 0 and i % long_pause_every == 0:
            LOGGER.info("长休眠 %.0fs (已完成 %d 篇)", long_pause_seconds, i)
            time.sleep(long_pause_seconds)
        elif delay:
            time.sleep(delay)

    # ── 最终报告 ──
    LOGGER.info("")
    LOGGER.info("=" * 60)
    LOGGER.info("最终统计报告")
    LOGGER.info("=" * 60)
    LOGGER.info("Elsevier DOI 总数:       %d", stats["total"])
    LOGGER.info("已有全文 PDF:            %d", stats["pdf_ok"])
    LOGGER.info("需要补 XML:              %d", stats["needs_xml"])
    LOGGER.info("已存在 XML:              %d", stats["xml_already_present"])
    LOGGER.info("本轮新下载 XML:          %d", stats["xml_downloaded"])
    LOGGER.info("XML 下载失败:            %d", stats["download_failed"])
    LOGGER.info("本轮新增成功:           %d", stats["xml_downloaded"])
    LOGGER.info("本轮新增失败:           %d", stats["download_failed"])
    LOGGER.info("累计成功 (含历史):       %d", len(status.success_dois))


def print_report(stats: dict, needs_xml_list: list[tuple[str, str, bool]]):
    """打印检测报告。"""
    print()
    print("=" * 60)
    print("Elsevier XML 补下载检测报告")
    print("=" * 60)
    print(f"Elsevier DOI 总数:   {stats['total']}")
    print(f"已有全文 PDF:        {stats['pdf_ok']}")
    print(f"需要补 XML:          {stats['needs_xml']}")
    print(f"已存在 XML:          {stats['xml_ready']}")
    print()

    if needs_xml_list:
        print("需要补 XML 的文献列表:")
        print("-" * 60)
        for doi, reason, xml_ready in needs_xml_list:
            state = "已有 XML" if xml_ready else "待下载"
            print(f"  {doi}  ({reason}, {state})")


if __name__ == "__main__":
    main()
