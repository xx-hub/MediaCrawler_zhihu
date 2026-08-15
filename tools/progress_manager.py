# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tools/progress_manager.py
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
import os
from typing import Dict, List, Optional, Set
from tools import utils


class ProgressManager:
    """进度管理器，用于实现断点续传功能"""
    
    def __init__(self, platform: str, crawler_type: str):
        self.platform = platform
        self.crawler_type = crawler_type
        self.progress_file = f"data/{self.platform}/progress_{self.crawler_type}.json"
        
    def _ensure_progress_dir(self):
        """确保进度文件目录存在"""
        try:
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        except OSError:
            pass
    
    def get_last_offset(self, url_token: str) -> int:
        """获取上次爬取的分页游标(page_offset)。

        知乎创作者回答 API 的 offset 为分页游标(0, 20, 40, ...),
        每次按 limit=20 递增。兼容读取旧字段名 last_offset。
        """
        self._ensure_progress_dir()
        
        if not os.path.exists(self.progress_file):
            return 0
            
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                user_progress = progress_data.get(url_token, {})
                # 优先新字段 page_offset,兼容旧字段 last_offset
                return int(user_progress.get('page_offset', user_progress.get('last_offset', 0)))
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return 0
    
    def save_progress(self, url_token: str, offset: int, total_count: int):
        """保存爬取进度。

        Args:
            url_token: 创作者 url_token
            offset: API 分页游标(每页 limit=20,循环内 offset += limit)
            total_count: 本次运行累计新增去重条数(非该作者回答总数)
        """
        self._ensure_progress_dir()
        
        progress_data = {}
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                progress_data = {}

        # 保留旧字段 last_offset/total_count 以向后兼容(新代码只读 page_offset/crawled_count)
        progress_data[url_token] = {
            'page_offset': offset,
            'crawled_count': total_count,
            'last_update': utils.get_current_timestamp(),
            'last_offset': offset,
            'total_count': total_count,
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    def get_existing_content_ids(self, item_type: str = "contents") -> Set[str]:
        """获取已存在的content_id集合，用于去重"""
        existing_ids = set()
        
        # 查找最新的JSON文件
        json_dir = f"data/{self.platform}/json"
        if not os.path.exists(json_dir):
            return existing_ids
            
        # 获取所有JSON文件
        try:
            json_files = [f for f in os.listdir(json_dir) if f.endswith('.json') and item_type in f]
        except OSError:
            return existing_ids
        if not json_files:
            return existing_ids
            
        # 按日期排序，取最新的文件
        latest_file = sorted(json_files)[-1]
        file_path = os.path.join(json_dir, latest_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if 'content_id' in item:
                            existing_ids.add(item['content_id'])
        except (json.JSONDecodeError, OSError, UnicodeDecodeError, KeyError):
            pass
            
        return existing_ids
    
    def is_content_crawled(self, url_token: str, content_id: str) -> bool:
        """检查内容是否已经爬取过"""
        self._ensure_progress_dir()
        
        if not os.path.exists(self.progress_file):
            return False
            
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                user_progress = progress_data.get(url_token, {})
                crawled_ids = user_progress.get('crawled_content_ids', [])
                return content_id in crawled_ids
        except (json.JSONDecodeError, OSError, UnicodeDecodeError, KeyError):
            return False
    
    def mark_content_crawled(self, url_token: str, content_id: str):
        """标记内容为已爬取"""
        self._ensure_progress_dir()
        
        progress_data = {}
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                progress_data = {}

        # 确保 url_token 键存在(不覆盖已有进度: 首次出现才初始化空字典)
        if url_token not in progress_data:
            progress_data[url_token] = {}

        if 'crawled_content_ids' not in progress_data[url_token]:
            progress_data[url_token]['crawled_content_ids'] = set()
        
        # 将set转换为list以便JSON序列化
        if isinstance(progress_data[url_token]['crawled_content_ids'], set):
            progress_data[url_token]['crawled_content_ids'] = list(progress_data[url_token]['crawled_content_ids'])
        
        # 添加新的content_id
        if content_id not in progress_data[url_token]['crawled_content_ids']:
            progress_data[url_token]['crawled_content_ids'].append(content_id)
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except OSError:
            utils.logger.warning(f"[ProgressManager.mark_content_crawled] 写入进度失败: {self.progress_file}")
    
    def clear_progress(self, url_token: Optional[str] = None):
        """清除进度记录"""
        if not os.path.exists(self.progress_file):
            return
            
        if url_token is None:
            # 清除所有进度
            try:
                os.remove(self.progress_file)
            except OSError:
                pass
        else:
            # 清除指定用户的进度
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                if url_token in progress_data:
                    del progress_data[url_token]
                    
                    with open(self.progress_file, 'w', encoding='utf-8') as f:
                        json.dump(progress_data, f, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError, KeyError):
                pass