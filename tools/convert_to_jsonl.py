#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert Zhihu JSON data to OpenAI fine-tuning JSONL format
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


def get_default_paths():
    """
    Get default input/output paths (relative to script location)
    Returns:
        tuple: (default_input, default_output, default_input_dir, default_output_dir)
    """
    # Script location: MediaCrawler/tools/convert_to_jsonl.py
    # main.py location: MediaCrawler/main.py (parent of tools/)

    script_dir = Path(__file__).parent
    media_crawler_dir = script_dir.parent

    # Default paths
    default_input = media_crawler_dir / 'data' / 'zhihu' / 'json' / 'creator_contents_2026-01-08.json'
    default_output = media_crawler_dir / 'data' / 'jsonl' / f'zhihu_qa_chatml_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl'
    default_input_dir = media_crawler_dir / 'data' / 'zhihu' / 'json'
    default_output_dir = media_crawler_dir / 'data' / 'jsonl'

    return default_input, default_output, default_input_dir, default_output_dir


def load_json_file(file_path: str) -> List[Dict]:
    """Load JSON file containing Zhihu answers"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def convert_to_openai_format(answer: Dict, include_system: bool = False, system_message: str = None) -> Optional[Dict]:
    """
    Convert a single Zhihu answer to OpenAI fine-tuning format

    Args:
        answer: Dictionary containing answer data
        include_system: Whether to include a system message
        system_message: Custom system message content

    Returns:
        Dictionary with messages array in OpenAI format, or None if invalid
    """
    # Extract question and answer
    question = answer.get('question_title', '').strip()
    answer_text = answer.get('content_text', '').strip()

    # Skip if question or answer is empty
    if not question or not answer_text:
        return None

    # Build messages array
    messages = []

    # Add system message if requested
    if include_system:
        default_system = "你是一个知识渊博的助手，擅长回答各种问题。"
        messages.append({
            "role": "system",
            "content": system_message if system_message else default_system
        })

    # Add user question
    messages.append({
        "role": "user",
        "content": question
    })

    # Add assistant answer
    messages.append({
        "role": "assistant",
        "content": answer_text
    })

    return {"messages": messages}


def save_jsonl(output_file: str, messages_list: List[Dict]):
    """
    Save messages to JSONL file in OpenAI fine-tuning format

    Args:
        output_file: Output file path
        messages_list: List of message dictionaries
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for messages in messages_list:
            # Each line is a JSON object with messages array
            json_line = json.dumps(messages, ensure_ascii=False)
            f.write(json_line + '\n')


def process_json_file(
    input_file: str,
    output_file: str,
    include_system: bool = False,
    system_message: str = None,
    max_samples: int = None
):
    """
    Process a single JSON file and convert to OpenAI fine-tuning JSONL format

    Args:
        input_file: Input JSON file path
        output_file: Output JSONL file path
        include_system: Whether to include system message
        system_message: Custom system message content
        max_samples: Maximum number of samples to convert
    """
    print(f"Reading from: {input_file}")

    # Load data
    data = load_json_file(input_file)
    print(f"Loaded {len(data)} records")

    # Convert each answer
    converted_messages = []

    for i, answer in enumerate(data):
        if max_samples and i >= max_samples:
            break

        messages = convert_to_openai_format(answer, include_system, system_message)

        if messages:
            converted_messages.append(messages)

            # Show progress every 100 records
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(data)} records...")

    print(f"Successfully converted {len(converted_messages)} records")

    # Save to JSONL
    save_jsonl(output_file, converted_messages)
    print(f"Saved to: {output_file}")
    print(f"Total lines: {len(converted_messages)}")


def batch_convert_directory(
    input_dir: str,
    output_dir: str,
    include_system: bool = False,
    system_message: str = None,
    pattern: str = "*.json"
):
    """
    Batch convert all JSON files in a directory

    Args:
        input_dir: Input directory containing JSON files
        output_dir: Output directory for JSONL files
        include_system: Whether to include system message
        system_message: Custom system message content
        pattern: File pattern to match
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all JSON files
    json_files = list(input_path.glob(pattern))

    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return

    print(f"Found {len(json_files)} JSON files")

    # Process each file
    for json_file in sorted(json_files):
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"zhihu_finetune_{timestamp}.jsonl"

        print(f"\nProcessing: {json_file.name}")
        print("-" * 60)

        try:
            process_json_file(str(json_file), str(output_file), include_system, system_message)
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")
            continue

    print("\n" + "=" * 60)
    print("Batch conversion completed!")


def main():
    """Main conversion function"""
    import argparse

    # Get default paths (relative to script location)
    default_input, default_output, default_input_dir, default_output_dir = get_default_paths()

    parser = argparse.ArgumentParser(
        description='Convert Zhihu JSON to OpenAI fine-tuning JSONL format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic conversion
  python tools/convert_to_jsonl.py

  # With system message
  python tools/convert_to_jsonl.py --include-system

  # Custom system message
  python tools/convert_to_jsonl.py --include-system --system-message "You are a helpful assistant."

  # Limit samples
  python tools/convert_to_jsonl.py --max-samples 100

  # Batch convert
  python tools/convert_to_jsonl.py --batch
        '''
    )
    parser.add_argument(
        '--input',
        type=str,
        default=str(default_input),
        help=f'Input JSON file path (default: data/zhihu/json/creator_contents_YYYY-MM-DD.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(default_output),
        help=f'Output JSONL file path (default: data/jsonl/zhihu_qa_chatml_YYYYMMDD_HHMMSS.jsonl)'
    )
    parser.add_argument(
        '--include-system',
        action='store_true',
        help='Include system message in conversations'
    )
    parser.add_argument(
        '--system-message',
        type=str,
        default=None,
        help='Custom system message content (only used with --include-system)'
    )
    parser.add_argument(
        '--max-samples',
        type=int,
        default=None,
        help='Maximum number of samples to convert'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Batch convert all JSON files in directory'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default=str(default_input_dir),
        help=f'Input directory for batch conversion (default: data/zhihu/json/)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=str(default_output_dir),
        help=f'Output directory for batch conversion (default: data/jsonl/)'
    )

    args = parser.parse_args()

    if args.batch:
        # Batch conversion mode
        print("Batch conversion mode")
        print("=" * 60)
        batch_convert_directory(
            args.input_dir,
            args.output_dir,
            args.include_system,
            args.system_message
        )
    else:
        # Single file conversion mode
        print("Single file conversion mode")
        print("=" * 60)
        if args.include_system and args.system_message:
            print(f"System message: {args.system_message}")
        elif args.include_system:
            print("System message: 你是一个知识渊博的助手，擅长回答各种问题。")

        process_json_file(
            args.input,
            args.output,
            args.include_system,
            args.system_message,
            args.max_samples
        )


if __name__ == "__main__":
    main()
