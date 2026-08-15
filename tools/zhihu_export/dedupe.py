# -*- coding: utf-8 -*-
"""
dedupe: 知乎内容去重工具。

迁移自根目录 deduplicate_zhihu.py,增强:
- 支持按 content_id 或 content_text 去重(默认 content_id)
- 输出报告:重复组数、去除条数
"""
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from .common import timestamp_str


def dedupe(
    input_path: Path,
    output_path: Optional[Path] = None,
    by: str = "content_id",
) -> int:
    """
    对 JSON 内容列表去重。

    Args:
        input_path: 输入 JSON 文件
        output_path: 输出文件;None 时在输入文件同目录生成 *_deduped_<时间戳>.json
        by: 去重键,content_id(推荐)或 content_text

    Returns:
        去除的重复条数
    """
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"无法读取 {input_path}: {e}") from e

    total_before = len(data)
    keys = [item.get(by, "") for item in data]
    key_counts = Counter(keys)
    dup_groups = {k: v for k, v in key_counts.items() if v > 1 and k}
    dup_count = sum(v - 1 for v in dup_groups.values())

    print(f"[dedupe] 去重前: {total_before} 条,按 {by} 去重")
    print(f"[dedupe] 重复键组数: {len(dup_groups)},需去除: {dup_count} 条")

    seen = set()
    deduped: List[Dict] = []
    for item in data:
        key = item.get(by, "")
        if not key or key not in seen:
            seen.add(key)
            deduped.append(item)

    total_after = len(deduped)
    print(f"[dedupe] 去重后: {total_after} 条,共去除 {total_before - total_after} 条")

    output_path = Path(output_path or (input_path.parent / f"{input_path.stem}_deduped_{timestamp_str()}.json"))
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(deduped, f, ensure_ascii=False, indent=4)
    except OSError as e:
        raise OSError(f"写入去重结果失败 {output_path}: {e}") from e
    print(f"[dedupe] 结果已保存: {output_path}")

    return total_before - total_after
