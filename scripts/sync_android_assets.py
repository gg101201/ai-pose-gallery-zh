"""把本地图库同步进 Android 工程，并把热链图片地址改写为本地路径。

用法（先执行 npx cap sync android，避免该命令清空补充资源）：
    python scripts/sync_android_assets.py

同步 data/、img/、thumbs/ 与站点根文件到 android/app/src/main/assets/public，
并在目标目录内改写两款热链服装的 JSON，使 App 完全离线。
仓库中的原始 JSON 不做修改，Web 部署行为不受影响。
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "android" / "app" / "src" / "main" / "assets" / "public"

MEDIA_DIRS = ("data", "img", "thumbs")
ROOT_FILES = ("og-cover.jpg", "robots.txt", "sitemap.xml", "_headers")

# 目标 JSON -> 需要本地化的图片 URL 规则（按顺序匹配）
REWRITES = {
    "data/costume-gia-anime-zh.json": (
        (re.compile(r"https://ai-costume-anime-gallery\.pages\.dev/thumbs/([^/]+\.webp)$"), r"thumbs/costumes/gia-anime/\1"),
        (re.compile(r"https://ai-costume-anime-gallery\.pages\.dev/img/([^/]+\.webp)$"), r"img/costumes/gia-anime/\1"),
        (re.compile(r"https://ai-costume-anime-gallery\.pages\.dev/png/([^/]+)\.png$"), r"img/costumes/gia-anime/\1.webp"),
    ),
    "data/costume-anime-zh.json": (
        (re.compile(r"https://charadb-2fi\.pages\.dev/thumb/([^/]+\.webp)$"), r"thumbs/costumes/charadb/\1"),
        (re.compile(r"https://charadb-2fi\.pages\.dev/img/([^/]+\.jpg)$"), r"img/costumes/charadb/\1"),
    ),
}

IMAGE_FIELDS = ("缩略图", "预览图", "原图")


def localize(value: str, rules: tuple[tuple[re.Pattern[str], str], ...]) -> tuple[str, bool]:
    for pattern, replacement in rules:
        if pattern.fullmatch(value):
            return pattern.sub(replacement, value), True
    return value, False


def rewrite_items(items: list[dict], rules: tuple[tuple[re.Pattern[str], str], ...]) -> int:
    changed = 0
    for item in items:
        for field in IMAGE_FIELDS:
            value = item.get(field)
            if isinstance(value, str):
                localized, hit = localize(value, rules)
                if hit:
                    item[field] = localized
                    changed += 1
        for view in item.get("views") or []:
            for field in IMAGE_FIELDS:
                value = view.get(field)
                if isinstance(value, str):
                    localized, hit = localize(value, rules)
                    if hit:
                        view[field] = localized
                        changed += 1
    return changed


def main() -> None:
    if not DEST.is_dir():
        raise SystemExit(f"找不到 {DEST}，请先执行 npx cap sync android")

    for name in MEDIA_DIRS:
        source = ROOT / name
        if not source.is_dir():
            raise SystemExit(f"缺少目录 {source}")
        shutil.copytree(source, DEST / name, dirs_exist_ok=True)
        files = sum(1 for path in (DEST / name).rglob("*") if path.is_file())
        print(f"同步 {name}/ -> {files} 个文件")

    for name in ROOT_FILES:
        source = ROOT / name
        if source.is_file():
            shutil.copy2(source, DEST / name)

    for relative, rules in REWRITES.items():
        path = DEST / relative
        items = json.loads(path.read_text(encoding="utf-8"))
        changed = rewrite_items(items, rules)
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"本地化 {relative} -> {changed} 个图片地址")

    missing = [
        item.get("缩略图")
        for relative in REWRITES
        for item in json.loads((DEST / relative).read_text(encoding="utf-8"))
        if isinstance(item.get("缩略图"), str)
        and not item["缩略图"].startswith("http")
        and not (DEST / item["缩略图"]).is_file()
    ]
    if missing:
        raise SystemExit(f"有 {len(missing)} 个缩略图未下载，示例：{missing[0]}")

    print("Android 资源同步完成，全部图片均为本地路径。")


if __name__ == "__main__":
    main()
