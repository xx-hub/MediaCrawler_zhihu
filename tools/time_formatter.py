# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tools/time_formatter.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。


import json
import datetime
from pathlib import Path
from typing import Dict, Any, List


def convert_timestamp_to_datetime(timestamp: int) -> str:
    """
    将Unix时间戳转换为yyyy-mm-dd tt:tt格式
    
    Args:
        timestamp: Unix时间戳（秒）
        
    Returns:
        str: 格式化的日期时间字符串，如"2026-01-01 14:58:02"
    """
    try:
        # 将秒级时间戳转换为datetime对象
        dt = datetime.datetime.fromtimestamp(timestamp)
        # 格式化为 yyyy-mm-dd tt:tt 格式
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"时间戳转换错误: {e}")
        return ""


def convert_millisecond_timestamp(timestamp: int) -> str:
    """
    将毫秒级Unix时间戳转换为yyyy-mm-dd tt:tt格式
    
    Args:
        timestamp: Unix时间戳（毫秒）
        
    Returns:
        str: 格式化的日期时间字符串
    """
    try:
        # 将毫秒转换为秒
        timestamp_seconds = timestamp // 1000
        return convert_timestamp_to_datetime(timestamp_seconds)
    except Exception as e:
        print(f"毫秒时间戳转换错误: {e}")
        return ""


def format_zhihu_data_file(file_path: str) -> None:
    """
    格式化知乎数据文件中的时间字段
    
    Args:
        file_path: 数据文件路径
    """
    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 处理每条数据
        formatted_count = 0
        for item in data:
            # 转换created_time
            if 'created_time' in item and item['created_time']:
                original_time = item['created_time']
                formatted_time = convert_timestamp_to_datetime(original_time)
                # 添加新字段，保留原字段
                item['created_time_formatted'] = formatted_time
                formatted_count += 1
            
            # 转换updated_time
            if 'updated_time' in item and item['updated_time']:
                original_time = item['updated_time']
                formatted_time = convert_timestamp_to_datetime(original_time)
                item['updated_time_formatted'] = formatted_time
                formatted_count += 1
            
            # 转换last_modify_ts（毫秒级）
            if 'last_modify_ts' in item and item['last_modify_ts']:
                original_time = item['last_modify_ts']
                formatted_time = convert_millisecond_timestamp(original_time)
                item['last_modify_ts_formatted'] = formatted_time
                formatted_count += 1
        
        # 保存格式化后的文件
        output_path = file_path.replace('.json', '_formatted.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"✅ 成功格式化 {formatted_count} 个时间字段")
        print(f"📁 新文件已保存为: {output_path}")
        
    except Exception as e:
        print(f"❌ 文件处理错误: {e}")


def format_single_timestamp(timestamp: int) -> str:
    """
    格式化单个时间戳（方便在代码中使用）
    
    Args:
        timestamp: Unix时间戳（秒）
        
    Returns:
        str: 格式化的日期时间字符串
    """
    return convert_timestamp_to_datetime(timestamp)


if __name__ == "__main__":
    # 示例用法
    example_timestamp = 1767237242
    formatted = format_single_timestamp(example_timestamp)
    print(f"示例时间戳转换: {example_timestamp} -> {formatted}")
    
    # 如果要格式化整个文件，取消下面的注释并修改文件路径
    # file_path = "data/zhihu/json/creator_contents_2026-01-01.json"
    # format_zhihu_data_file(file_path)