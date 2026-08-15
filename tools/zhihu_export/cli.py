# -*- coding: utf-8 -*-
"""
zhihu_export 统一命令行入口。

用法:
    python -m tools.zhihu_export.cli export-md   [--input FILE] [--output DIR] [--merge] [--limit N]
    python -m tools.zhihu_export.cli export-jsonl [--input FILE] [--output FILE] [--merge]
                                                  [--include-system] [--system-message MSG]
                                                  [--min-length N] [--max-length N] [--min-votes N] [--max-samples N]
    python -m tools.zhihu_export.cli dedupe      [--input FILE] [--output FILE] [--by content_id|content_text]
    python -m tools.zhihu_export.cli analyze     [--md-dir DIR] [--output-dir DIR] [--author NAME]
    python -m tools.zhihu_export.cli merge       [--input-dir DIR] [--output FILE]

示例:
    # 合并所有快照并导出 Markdown(试跑 20 条)
    python -m tools.zhihu_export.cli export-md --merge --limit 20

    # 导出微调数据集(正文 >= 100 字,赞同 >= 10,包含问题描述)
    python -m tools.zhihu_export.cli export-jsonl --merge --min-length 100 --min-votes 10

    # 思维逻辑分析
    python -m tools.zhihu_export.cli analyze --md-dir data/zhihu/md-canglimo --author 墨苍离
"""
# pyright: reportMissingImports=false, reportAttributeAccessIssue=false
# 说明: pyright 在此环境下无法读取本包部分子模块内容(映射盘路径缺陷),
# 运行时已验证所有导入正常(python -m tools.zhihu_export.cli 可用)。

import argparse
from pathlib import Path
from typing import Dict, Optional

from . import __version__
from . import analyze, dedupe, export_jsonl, export_md  # 通过包命名空间导入,规避 pyright 模块解析缺陷
from .common import (
    default_analysis_dir,
    default_json_dir,
    default_jsonl_dir,
    default_md_dir,
    load_merged_contents,
    timestamp_str,
)


def _add_input_output_args(parser: argparse.ArgumentParser, json_input: bool = True) -> None:
    if json_input:
        parser.add_argument(
            "--input", type=Path, default=None,
            help="输入 JSON 文件;配合 --merge 时为快照目录",
        )
    else:
        parser.add_argument(
            "--md-dir", type=Path, default=None,
            help=f"Markdown 目录(默认: {default_md_dir()})",
        )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="输出文件/目录(默认见各子命令说明)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zhihu_export",
        description="知乎数据导出工具包(export-md / export-jsonl / dedupe / analyze / merge)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # export-md
    p_md = sub.add_parser("export-md", help="JSON -> Markdown 单文件问答格式")
    p_md.add_argument("--input", type=Path, default=None, help="输入 JSON 文件")
    p_md.add_argument("--output", type=Path, default=None, help=f"输出目录(默认: {default_md_dir()})")
    p_md.add_argument("--merge", action="store_true", help="合并 json 目录下全部快照后导出(增量去重)")
    p_md.add_argument("--content-type", default="answer", choices=["answer", "article", "zvideo"],
                      help="只导出该类型内容(默认 answer)")
    p_md.add_argument("--nickname", default=None, help="只导出该作者的回答(user_nickname 精确匹配)")
    p_md.add_argument("--limit", type=int, default=None, help="最多导出条数(试跑用)")
    p_md.set_defaults(func=cmd_export_md)

    # export-jsonl
    p_jl = sub.add_parser("export-jsonl", help="JSON -> OpenAI fine-tuning JSONL(ChatML)")
    p_jl.add_argument("--input", type=Path, default=None, help="输入 JSON 文件")
    p_jl.add_argument("--output", type=Path, default=None,
                      help=f"输出文件(默认: {default_jsonl_dir()}/zhihu_qa_chatml_<时间戳>.jsonl)")
    p_jl.add_argument("--merge", action="store_true", help="合并 json 目录下全部快照后导出")
    p_jl.add_argument("--include-system", action="store_true", help="包含 system 消息")
    p_jl.add_argument("--system-message", default=None, help="自定义 system 消息内容")
    p_jl.add_argument("--min-length", type=int, default=0, help="回答正文最少字数(默认 0)")
    p_jl.add_argument("--max-length", type=int, default=None, help="回答正文最多字数")
    p_jl.add_argument("--min-votes", type=int, default=0, help="最低赞同数(默认 0)")
    p_jl.add_argument("--max-samples", type=int, default=None, help="最多转换条数")
    p_jl.set_defaults(func=cmd_export_jsonl)

    # dedupe
    p_dd = sub.add_parser("dedupe", help="按 content_id / content_text 去重")
    p_dd.add_argument("--input", type=Path, required=True, help="输入 JSON 文件")
    p_dd.add_argument("--output", type=Path, default=None, help="输出文件(默认: 同目录 *_deduped_<时间戳>.json)")
    p_dd.add_argument("--by", default="content_id", choices=["content_id", "content_text"],
                      help="去重键(默认 content_id)")
    p_dd.set_defaults(func=cmd_dedupe)

    # analyze
    p_an = sub.add_parser("analyze", help="对 Markdown 回答做思维逻辑分析")
    p_an.add_argument("--md-dir", type=Path, default=None, help=f"Markdown 目录(默认: {default_md_dir()})")
    p_an.add_argument("--output-dir", type=Path, default=None, help=f"输出目录(默认: {default_analysis_dir()})")
    p_an.add_argument("--author", default="知乎回答", help="分析对象名称(用于报告标题)")
    p_an.set_defaults(func=cmd_analyze)

    # merge
    p_mg = sub.add_parser("merge", help="增量合并多个 JSON 快照(按 content_id 去重)")
    p_mg.add_argument("--input-dir", type=Path, default=None, help=f"快照目录(默认: {default_json_dir()})")
    p_mg.add_argument("--output", type=Path, default=None,
                      help=f"输出文件(默认: {default_json_dir()}/creator_contents_merged_<时间戳>.json)")
    p_mg.set_defaults(func=cmd_merge)

    return parser


def cmd_export_md(args: argparse.Namespace) -> int:
    return export_md.export_to_md(
        input_path=args.input,
        output_dir=args.output,
        merge_snapshots=args.merge,
        content_type=args.content_type,
        nickname=args.nickname,
        limit=args.limit,
    )


def cmd_export_jsonl(args: argparse.Namespace) -> int:
    return export_jsonl.export_to_jsonl(
        input_path=args.input,
        output_path=args.output,
        merge_snapshots=args.merge,
        include_system=args.include_system,
        system_message=args.system_message,
        min_length=args.min_length,
        max_length=args.max_length,
        min_votes=args.min_votes,
        max_samples=args.max_samples,
    )


def cmd_dedupe(args: argparse.Namespace) -> int:
    # 延迟导入: 规避 pyright 对同名模块/函数(dedupe.dedupe)的解析缺陷
    from .dedupe import dedupe as run_dedupe
    return run_dedupe(input_path=args.input, output_path=args.output, by=args.by)


def cmd_analyze(args: argparse.Namespace) -> Dict:
    # 延迟导入: 规避 pyright 对同名模块/函数(analyze.analyze)的解析缺陷
    from .analyze import analyze as run_analyze
    return run_analyze(md_dir=args.md_dir, output_dir=args.output_dir, author=args.author)


def cmd_merge(args: argparse.Namespace) -> int:
    merged = load_merged_contents(args.input_dir)
    output = Path(args.output or (default_json_dir() / f"creator_contents_merged_{timestamp_str()}.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    import json
    output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[merge] 已保存: {output} ({len(merged)} 条)")
    return len(merged)


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
