# -*- coding: utf-8 -*-
"""
zhihu_export 公共工具:路径默认值、图片占位符清理、文件名清洗、快照合并加载。
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# 路径默认值(相对仓库根目录)
# ---------------------------------------------------------------------------
REPO_DIR = Path(__file__).resolve().parent.parent.parent


def default_json_dir() -> Path:
    """默认 JSON 快照目录: data/zhihu/json/"""
    return REPO_DIR / "data" / "zhihu" / "json"


def default_md_dir() -> Path:
    """默认 Markdown 输出目录: data/zhihu/md/"""
    return REPO_DIR / "data" / "zhihu" / "md"


def default_jsonl_dir() -> Path:
    """默认 JSONL 输出目录: data/jsonl/"""
    return REPO_DIR / "data" / "jsonl"


def default_analysis_dir() -> Path:
    """默认分析输出目录: data/zhihu/analysis/"""
    return REPO_DIR / "data" / "zhihu" / "analysis"


# ---------------------------------------------------------------------------
# 图片占位符处理
# ---------------------------------------------------------------------------
# 知乎正文提取时,有效图片被替换为 [图片N] 并收集进 images 列表;
# 无法提取 URL 的 img 标签现在会被直接丢弃(见 tools/crawler_util.py)。
# 这里负责把残留占位符做最终清理:有 URL 则替换,无 URL 则删除。
IMG_INDEXED_PLACEHOLDER_RE = re.compile(r"\[图片(\d+)\]")
# 裸占位符:负向断言避免二次匹配自身生成的 ![图片](url)
IMG_BARE_PLACEHOLDER_RE = re.compile(r"\[图片\](?!\()")
IMG_MARKDOWN_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def cleanup_image_placeholders(text: str, images: Optional[List[str]] = None) -> str:
    """
    把正文中的图片占位符替换为 Markdown 图片。

    - [图片N] 按索引对应 images[N-1],索引越界则删除该占位符;
    - 裸 [图片] 按顺序消费 images,列表耗尽则删除。
    """
    if not text:
        return text
    images = images or []
    used = 0  # 已消费的图片数(索引与裸占位符共享)

    def replace_indexed(match: "re.Match") -> str:
        nonlocal used
        try:
            index = int(match.group(1)) - 1
        except ValueError:
            return ""  # 非数字索引:删除
        if 0 <= index < len(images):
            used += 1
            return f"![图片]({images[index]})"
        return ""  # 无对应 URL:删除,避免泄漏

    text = IMG_INDEXED_PLACEHOLDER_RE.sub(replace_indexed, text)

    def replace_bare(match: "re.Match") -> str:
        nonlocal used
        if used < len(images):
            url = images[used]
            used += 1
            return f"![图片]({url})"
        return ""  # 列表耗尽:删除

    return IMG_BARE_PLACEHOLDER_RE.sub(replace_bare, text)


def strip_image_markdown(text: str) -> str:
    """
    剔除 Markdown 图片语法 ![](url) 及裸露占位符。
    用于微调数据集 / 文本统计:图片信息无法进入纯文本,直接移除最干净。
    """
    if not text:
        return text
    text = IMG_MARKDOWN_RE.sub("", text)
    text = IMG_INDEXED_PLACEHOLDER_RE.sub("", text)
    text = IMG_BARE_PLACEHOLDER_RE.sub("", text)
    # 清理删除后遗留的空行
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# 文件与文本工具
# ---------------------------------------------------------------------------
def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """清理文件名中的非法字符并限制长度(Windows 安全)。"""
    filename = re.sub(r'[\\/:*?"<>|]', "_", filename)
    return filename.strip()[:max_length]


def load_json_file(path: Path) -> List[Dict]:
    """读取 JSON 文件(内容列表),失败时抛出带文件名的 ValueError。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"无法读取 {path}: {e}") from e
    if not isinstance(data, list):
        raise ValueError(f"{path} 不是列表格式的 JSON")
    return data


def load_merged_contents(json_dir: Optional[Path] = None) -> List[Dict]:
    """
    增量合并 json_dir 下所有 creator_contents_*.json 快照。

    按 content_id 去重,后写入的快照(更新)覆盖旧快照,
    实现"多次爬取 -> 一份完整数据"而不需要全量重爬。
    """
    json_dir = Path(json_dir or default_json_dir())
    if not json_dir.exists():
        return []

    files = sorted(
        f for f in json_dir.glob("creator_contents_*.json")
        if not f.name.endswith("_deduped.json")  # 跳过历史去重产物
    )
    merged: Dict[str, Dict] = {}
    for f in files:
        try:
            for item in load_json_file(f):
                cid = item.get("content_id")
                if cid:
                    merged[cid] = item  # 同名覆盖,保留最新快照
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[merge] 跳过 {f.name}: {e}")
    print(f"[merge] 合并 {len(files)} 个快照,共 {len(merged)} 条唯一内容")
    return list(merged.values())


def timestamp_str() -> str:
    """当前时间戳,用于文件名: YYYYMMDD_HHMMSS"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
