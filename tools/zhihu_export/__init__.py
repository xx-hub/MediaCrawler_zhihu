# -*- coding: utf-8 -*-
"""
zhihu_export: 知乎数据导出工具包

提供知乎爬取数据的统一后处理管线:
    export-md       JSON -> Markdown(单文件问答格式)
    export-jsonl    JSON -> OpenAI fine-tuning JSONL(ChatML)
    dedupe          按 content_id / content_text 去重
    analyze         对 Markdown 回答做思维逻辑分析,生成报告
    merge           增量合并多个 JSON 快照

用法:
    python -m tools.zhihu_export.cli export-md --help
"""

__version__ = "1.0.0"

# 预导入子模块:保证 python -m tools.zhihu_export.cli 与 IDE 类型解析一致
from . import analyze, common, dedupe, export_jsonl, export_md  # noqa: F401
