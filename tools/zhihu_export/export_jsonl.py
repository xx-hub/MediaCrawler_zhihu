# -*- coding: utf-8 -*-
"""
export_jsonl: 知乎内容 JSON -> OpenAI fine-tuning JSONL(ChatML)。

迁移自 tools/convert_to_jsonl.py,增强:
- user 消息 = 问题标题 + 问题描述(完整提问上下文)
- 质量过滤:内容类型、正文长度、赞同数
- 图片占位符/图片语法剔除(纯文本微调数据不需要图片)
- 支持增量合并快照(--merge)
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .common import (
    default_jsonl_dir,
    load_json_file,
    load_merged_contents,
    strip_image_markdown,
    timestamp_str,
)

DEFAULT_SYSTEM_MESSAGE = "你是一个知识渊博的助手，擅长回答各种问题。"


def convert_to_openai_format(
    answer: Dict,
    include_system: bool = False,
    system_message: Optional[str] = None,
    min_length: int = 0,
    max_length: Optional[int] = None,
    min_votes: int = 0,
) -> Optional[Dict]:
    """
    将单条知乎回答转换为 OpenAI 微调格式。

    user = 问题标题(+ 问题描述)
    assistant = 回答正文(剔除图片,清理占位符)

    返回 None 表示该条不满足过滤条件。
    """
    question = (answer.get("question_title") or "").strip()
    question_detail = (answer.get("question_detail") or "").strip()
    answer_text = (answer.get("content_text") or "").strip()

    if not question or not answer_text:
        return None
    if answer.get("content_type", "answer") != "answer":
        return None
    if len(answer_text) < min_length:
        return None
    if max_length is not None and len(answer_text) > max_length:
        return None
    if (answer.get("voteup_count") or 0) < min_votes:
        return None

    # 剔除图片信息,清理残留占位符
    answer_text = strip_image_markdown(answer_text)
    question_detail = strip_image_markdown(question_detail)

    messages: List[Dict[str, str]] = []
    if include_system:
        messages.append({
            "role": "system",
            "content": system_message or DEFAULT_SYSTEM_MESSAGE,
        })

    # 问题描述并入 user 消息,提供更完整的提问上下文;
    # 若描述与标题重复(知乎常见 detail==title),避免冗余拼接
    user_content = question
    if question_detail and question_detail != question and question_detail not in question:
        user_content = f"{question}\n\n{question_detail}"

    messages.append({"role": "user", "content": user_content})
    messages.append({"role": "assistant", "content": answer_text})

    return {"messages": messages}


def save_jsonl(output_file: Path, messages_list: List[Dict]) -> None:
    """写入 JSONL 文件(OpenAI fine-tuning 格式)。"""
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            for messages in messages_list:
                f.write(json.dumps(messages, ensure_ascii=False) + "\n")
    except OSError as e:
        raise OSError(f"写入 JSONL 失败 {output_file}: {e}") from e


def export_to_jsonl(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    merge_snapshots: bool = False,
    include_system: bool = False,
    system_message: Optional[str] = None,
    min_length: int = 0,
    max_length: Optional[int] = None,
    min_votes: int = 0,
    max_samples: Optional[int] = None,
) -> int:
    """
    导出知乎内容为 OpenAI fine-tuning JSONL。

    Args:
        input_path: 单个 JSON 文件;None 且 merge_snapshots=True 时合并全部快照
        output_path: 输出文件,默认 data/jsonl/zhihu_qa_chatml_<时间戳>.jsonl
        merge_snapshots: 合并 json 目录下所有 creator_contents_*.json 快照
        include_system: 是否包含 system 消息
        system_message: 自定义 system 消息内容
        min_length / max_length: 回答正文字数过滤
        min_votes: 最低赞同数过滤
        max_samples: 最多转换条数

    Returns:
        实际写入的样本数
    """
    if merge_snapshots:
        data = load_merged_contents(input_path.parent if input_path else None)
    else:
        if input_path is None:
            raise ValueError("需要指定 --input 或使用 --merge 合并目录快照")
        data = load_json_file(Path(input_path))

    output_path = Path(output_path or (default_jsonl_dir() / f"zhihu_qa_chatml_{timestamp_str()}.jsonl"))

    converted: List[Dict] = []
    for i, answer in enumerate(data):
        if max_samples is not None and len(converted) >= max_samples:
            break
        messages = convert_to_openai_format(
            answer,
            include_system=include_system,
            system_message=system_message,
            min_length=min_length,
            max_length=max_length,
            min_votes=min_votes,
        )
        if messages:
            converted.append(messages)
            if (i + 1) % 1000 == 0:
                print(f"[export-jsonl] 已处理 {i + 1}/{len(data)} 条 ...")

    save_jsonl(output_path, converted)
    print(f"[export-jsonl] 完成,共 {len(converted)} 条 -> {output_path}")
    return len(converted)
