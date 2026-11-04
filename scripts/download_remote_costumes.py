"""把热链服装图下载到本地，供 Android 离线包使用。

- ギア动漫（1320 套）：下载 /thumbs/*.webp 与 /img/*.webp。
  原图 PNG 与 WebP 的分辨率一致（512x768），PNG 仅体积大 8 倍，故不下载。
- CharaDB（440 套）：下载 /thumb/*.webp 与 /img/*.jpg（1024x1536）。

图片写入 img/costumes/<group>/ 与 thumbs/costumes/<group>/，可重复执行（已存在且
格式正确的文件会跳过）。失败清单写入 download_failed.txt。
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import time
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ai-pose-gallery-zh offline bundler"

GROUPS = (
    {
        "name": "gia-anime",
        "data": ROOT / "data" / "costume-gia-anime-zh.json",
        "thumb_field": "缩略图",
        "main_field": "预览图",
    },
    {
        "name": "charadb",
        "data": ROOT / "data" / "costume-anime-zh.json",
        "thumb_field": "缩略图",
        "main_field": "预览图",
    },
)


def image_name(url: str) -> str:
    name = unquote(Path(urlparse(url).path).name)
    if not name:
        raise ValueError(f"无法解析图片文件名: {url}")
    return name


def is_image(data: bytes) -> bool:
    return (data[:4] == b"RIFF" and data[8:12] == b"WEBP") or data[:2] == b"\xff\xd8"


def is_valid(path: Path) -> bool:
    try:
        if path.stat().st_size < 100:
            return False
        with path.open("rb") as handle:
            return is_image(handle.read(12))
    except OSError:
        return False


def download(url: str, dest: Path, retries: int = 4) -> str:
    if is_valid(dest):
        return "skip"
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            if not is_image(data):
                raise ValueError("响应不是有效图片")
            dest.parent.mkdir(parents=True, exist_ok=True)
            temp = dest.with_suffix(dest.suffix + ".part")
            temp.write_bytes(data)
            temp.replace(dest)
            return "ok"
        except Exception as exc:  # 网络抖动、超时、5xx 都重试
            last_error = exc
            time.sleep(min(2 ** attempt, 8))
    return f"fail: {type(last_error).__name__}: {last_error}"


def collect_tasks() -> list[tuple[str, Path]]:
    tasks: dict[Path, str] = {}
    for group in GROUPS:
        items = json.loads(group["data"].read_text(encoding="utf-8"))
        for item in items:
            thumb = item.get(group["thumb_field"])
            main = item.get(group["main_field"])
            if not thumb or not main:
                continue
            tasks[ROOT / "thumbs" / "costumes" / group["name"] / image_name(thumb)] = thumb
            tasks[ROOT / "img" / "costumes" / group["name"] / image_name(main)] = main
    return [(url, dest) for dest, url in tasks.items()]


def main() -> int:
    parser = argparse.ArgumentParser(description="下载热链服装图到本地")
    parser.add_argument("--workers", type=int, default=16, help="并发下载数（默认 16）")
    args = parser.parse_args()

    tasks = collect_tasks()
    total = len(tasks)
    print(f"待处理 {total} 个文件，并发 {args.workers}")

    counts = {"ok": 0, "skip": 0, "fail": 0}
    failures: list[tuple[str, str]] = []
    started = time.time()
    with futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        pending = {pool.submit(download, url, dest): (url, dest) for url, dest in tasks}
        for index, future in enumerate(futures.as_completed(pending), start=1):
            url, dest = pending[future]
            try:
                result = future.result()
            except Exception as exc:  # 理论上下载函数不会抛出
                result = f"fail: {type(exc).__name__}: {exc}"
            key = result if result in counts else "fail"
            counts[key] += 1
            if key == "fail":
                failures.append((url, result))
            if index % 100 == 0 or index == total:
                elapsed = max(time.time() - started, 0.1)
                print(
                    f"[{index}/{total}] ok={counts['ok']} skip={counts['skip']} "
                    f"fail={counts['fail']} {index / elapsed:.1f} 文件/秒"
                )

    if failures:
        log = ROOT / "download_failed.txt"
        log.write_text("\n".join(f"{result}\t{url}" for url, result in failures) + "\n", encoding="utf-8")
        print(f"\n失败 {len(failures)} 个，清单见 {log}")
    print(
        f"完成：新增 {counts['ok']}，已存在 {counts['skip']}，失败 {counts['fail']}，"
        f"耗时 {time.time() - started:.0f}s"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
