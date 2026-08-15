# -*- coding: utf-8 -*-
"""
export_md: 知乎内容 JSON -> Markdown 单文件问答格式。

迁移自 data/zhihu/scripts/convert_to_zhihu_md.py,增强:
- 图片占位符兜底清理(无 URL 的占位符删除,不再泄漏)
- 支持增量合并多个快照(--merge)
- 支持 --limit 试跑、--content-type 过滤
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .common import (
    cleanup_image_placeholders,
    default_md_dir,
    load_json_file,
    load_merged_contents,
    sanitize_filename,
)


def build_md_content(item: Dict) -> Optional[str]:
    """将单条知乎内容转换为 Markdown 文本;非回答或无标题内容返回 None。"""
    content_type = item.get("content_type", "")
    question_title = item.get("question_title", "")
    if content_type != "answer" or not question_title:
        return None

    question_detail = item.get("question_detail", "") or ""
    content_text = item.get("content_text", "") or ""
    user_nickname = item.get("user_nickname", "") or ""
    voteup_count = item.get("voteup_count", 0)
    comment_count = item.get("comment_count", 0)
    content_url = item.get("content_url", "") or ""
    content_id = item.get("content_id", "") or ""
    created_time = item.get("created_time", 0) or 0
    images = item.get("images", []) or []

    # 占位符兜底:有 URL 替换为 Markdown 图片,无 URL 直接删除
    content_text = cleanup_image_placeholders(content_text, images)
    # 问题描述可能带知乎原文的 [图片] alt 文本,同样兜底清理
    question_detail = cleanup_image_placeholders(question_detail, images)

    lines: List[str] = []
    lines.append(f"# {question_title}")
    lines.append("")

    if question_detail:
        lines.append("## 问题描述")
        lines.append("")
        lines.append(question_detail)
        lines.append("")

    lines.append(f"## 回答者：{user_nickname}")
    lines.append(f"- 赞同数：{voteup_count}")
    lines.append(f"- 评论数：{comment_count}")
    lines.append(f"- 回答链接：[{content_url}]({content_url})")
    lines.append(f"- 回答ID：{content_id}")
    lines.append("")

    lines.append("## 回答内容")
    lines.append("")
    if content_text:
        lines.append(content_text)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"整理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)


def make_filename(item: Dict) -> str:
    """生成文件名: 日期_问题标题_回答ID前8位.md"""
    created_time = item.get("created_time", 0) or 0
    question_title = item.get("question_title", "") or ""
    content_id = item.get("content_id", "") or ""
    if created_time:
        date_str = datetime.fromtimestamp(created_time).strftime("%Y-%m-%d")
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    title_part = sanitize_filename(question_title[:50], max_length=50)
    return f"{date_str}_{title_part}_{content_id[:8]}.md"


def export_to_md(
    input_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    merge_snapshots: bool = False,
    content_type: str = "answer",
    nickname: Optional[str] = None,
    limit: Optional[int] = None,
) -> int:
    """
    导出 JSON 快照为 Markdown 文件。

    Args:
        input_path: 单个 JSON 文件;为 None 且 merge_snapshots=True 时合并目录下全部快照
        output_dir: 输出目录,默认 data/zhihu/md
        merge_snapshots: 合并 json 目录下所有 creator_contents_*.json 快照(增量去重)
        content_type: 只导出该类型(answer | article | zvideo)
        nickname: 只导出该作者(user_nickname 精确匹配)的回答
        limit: 最多导出条数(用于试跑)

    Returns:
        实际导出的文件数
    """
    output_dir = Path(output_dir or default_md_dir())
    output_dir.mkdir(parents=True, exist_ok=True)

    if merge_snapshots:
        data = load_merged_contents(input_path.parent if input_path else None)
    else:
        if input_path is None:
            raise ValueError("需要指定 --input 或使用 --merge 合并目录快照")
        data = load_json_file(Path(input_path))

    # 按创建时间倒序(最新在前),与旧脚本行为一致
    sorted_data = sorted(data, key=lambda x: x.get("created_time", 0), reverse=True)

    processed = 0
    for item in sorted_data:
        if item.get("content_type", "") != content_type:
            continue
        if nickname and item.get("user_nickname", "") != nickname:
            continue
        if limit is not None and processed >= limit:
            break

        md_content = build_md_content(item)
        if md_content is None:
            continue

        output_file = output_dir / make_filename(item)
        output_file.write_text(md_content, encoding="utf-8")
        processed += 1
        if processed % 500 == 0:
            print(f"[export-md] 已导出 {processed} 个文件 ...")

    print(f"[export-md] 完成,共导出 {processed} 个文件 -> {output_dir}")
    return processed


if __name__ == "__main__":  # pragma: no cover
    # 直接运行时提供简单的默认行为;统一入口请使用 cli.py
    export_to_md(merge_snapshots=True, limit=10)
