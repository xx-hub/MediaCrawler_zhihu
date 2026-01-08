# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tools/desc_fixer.py
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
import re
from pathlib import Path
from typing import Dict, Any, List


def restore_desc_newlines(data_file: str) -> None:
    """
    修复desc字段的换行问题，从content_text中提取并恢复正确的换行格式
    
    Args:
        data_file: 数据文件路径
    """
    try:
        # 读取JSON文件
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        fixed_count = 0
        
        # 处理每条数据
        for item in data:
            if 'desc' in item and 'content_text' in item:
                original_desc = item['desc']
                content_text = item['content_text']
                
                # 如果desc是content_text的简化版本，尝试恢复换行
                if original_desc and content_text:
                    # 方法1: 从content_text中提取前几行作为desc
                    content_lines = content_text.split('\n')
                    if len(content_lines) > 1:
                        # 取前3行作为desc，保持换行
                        new_desc_lines = []
                        for line in content_lines[:3]:
                            line = line.strip()
                            if line:  # 跳过空行
                                new_desc_lines.append(line)
                        
                        if new_desc_lines:
                            new_desc = '\n'.join(new_desc_lines)
                            # 如果原始desc没有换行，但新desc有，则替换
                            if '\n' not in original_desc and '\n' in new_desc:
                                item['desc'] = new_desc
                                fixed_count += 1
                                print(f"✅ 修复desc字段: {original_desc[:50]}... -> {new_desc[:50]}...")
                    
                    # 方法2: 如果desc是content_text的前面部分，尝试匹配并恢复换行
                    elif original_desc in content_text:
                        # 找到desc在content_text中的位置
                        start_pos = content_text.find(original_desc)
                        if start_pos != -1:
                            # 获取desc所在行的完整内容
                            line_start = content_text.rfind('\n', 0, start_pos) + 1
                            line_end = content_text.find('\n', start_pos)
                            if line_end == -1:
                                line_end = len(content_text)
                            
                            full_line = content_text[line_start:line_end].strip()
                            if full_line and full_line != original_desc:
                                item['desc'] = full_line
                                fixed_count += 1
                                print(f"✅ 修复desc字段: {original_desc[:50]}... -> {full_line[:50]}...")
        
        # 保存修复后的文件
        output_path = data_file.replace('.json', '_fixed.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"\n✅ 成功修复 {fixed_count} 个desc字段")
        print(f"📁 修复后的文件已保存为: {output_path}")
        
    except Exception as e:
        print(f"❌ 文件处理错误: {e}")


def enhance_desc_with_newlines(data_file: str) -> None:
    """
    增强desc字段，确保其有适当的换行格式
    
    Args:
        data_file: 数据文件路径
    """
    try:
        # 读取JSON文件
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        enhanced_count = 0
        
        # 处理每条数据
        for item in data:
            if 'desc' in item and item['desc']:
                original_desc = item['desc']
                
                # 如果desc没有换行，尝试添加合适的换行
                if '\n' not in original_desc:
                    # 根据标点符号添加换行
                    enhanced_desc = original_desc
                    
                    # 在句号后添加换行
                    enhanced_desc = re.sub(r'([。！？])\s*', r'\1\n', enhanced_desc)
                    
                    # 如果内容太长，在适当位置添加换行
                    if len(enhanced_desc) > 100:
                        # 找到第一个逗号或分号后的位置
                        first_comma = enhanced_desc.find('，')
                        first_semicolon = enhanced_desc.find('；')
                        
                        split_pos = -1
                        if first_comma != -1 and first_comma < 80:
                            split_pos = first_comma
                        elif first_semicolon != -1 and first_semicolon < 80:
                            split_pos = first_semicolon
                        
                        if split_pos != -1:
                            enhanced_desc = enhanced_desc[:split_pos+1] + '\n' + enhanced_desc[split_pos+1:]
                    
                    if enhanced_desc != original_desc:
                        item['desc'] = enhanced_desc
                        enhanced_count += 1
                        print(f"✅ 增强desc字段: {original_desc[:50]}... -> {enhanced_desc[:50]}...")
        
        # 保存增强后的文件
        output_path = data_file.replace('.json', '_enhanced.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"\n✅ 成功增强 {enhanced_count} 个desc字段")
        print(f"📁 增强后的文件已保存为: {output_path}")
        
    except Exception as e:
        print(f"❌ 文件处理错误: {e}")


def create_new_desc_with_newlines(data_file: str) -> None:
    """
    创建新的desc字段，从content_text中提取前几行并保持换行格式
    
    Args:
        data_file: 数据文件路径
    """
    try:
        # 读取JSON文件
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        created_count = 0
        
        # 处理每条数据
        for item in data:
            if 'content_text' in item and item['content_text']:
                content_text = item['content_text']
                
                # 从content_text中提取前3行作为新的desc
                lines = content_text.split('\n')
                new_desc_lines = []
                
                for line in lines[:3]:  # 取前3行
                    line = line.strip()
                    if line:  # 跳过空行
                        new_desc_lines.append(line)
                        if len(new_desc_lines) >= 3:  # 最多3行
                            break
                
                if new_desc_lines:
                    new_desc = '\n'.join(new_desc_lines)
                    # 添加新字段，保留原字段
                    item['desc_new'] = new_desc
                    created_count += 1
                    print(f"✅ 创建新desc字段: {new_desc[:50]}...")
        
        # 保存包含新字段的文件
        output_path = data_file.replace('.json', '_with_new_desc.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"\n✅ 成功创建 {created_count} 个新desc字段")
        print(f"📁 新文件已保存为: {output_path}")
        
    except Exception as e:
        print(f"❌ 文件处理错误: {e}")


if __name__ == "__main__":
    # 示例用法
    file_path = "data/zhihu/json/creator_contents_2026-01-01.json"
    
    print("1. 修复desc字段换行问题:")
    restore_desc_newlines(file_path)
    
    print("\n2. 增强desc字段格式:")
    enhance_desc_with_newlines(file_path)
    
    print("\n3. 创建新的desc字段:")
    create_new_desc_with_newlines(file_path)