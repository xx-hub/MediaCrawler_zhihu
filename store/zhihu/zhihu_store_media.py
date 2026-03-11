# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/store/zhihu/zhihu_store_media.py
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

import pathlib
import httpx
import asyncio
from typing import Dict, List

import aiofiles

from base.base_crawler import AbstractStoreImage
from tools import utils


class ZhihuImage(AbstractStoreImage):
    image_store_path: str = "data/zhihu/images"

    async def store_image(self, image_content_item: Dict):
        """
        store content

        Args:
            image_content_item:

        Returns:

        """
        await self.save_image(image_content_item.get("content_id"), image_content_item.get("image_url"))

    def make_save_file_name(self, content_id: str, image_url: str) -> str:
        """
        make save file name by store type

        Args:
            content_id: content id
            image_url: image url

        Returns:

        """
        # 从URL中提取文件名
        import urllib.parse
        parsed_url = urllib.parse.urlparse(image_url)
        filename = parsed_url.path.split("/")[-1]
        if not filename:
            filename = f"image_{utils.get_current_timestamp()}.jpg"
        return f"{self.image_store_path}/{content_id}/{filename}"

    async def save_image(self, content_id: str, image_url: str):
        """
        save image to local

        Args:
            content_id: content id
            image_url: image url

        Returns:

        """
        try:
            # 创建存储目录
            pathlib.Path(self.image_store_path + "/" + content_id).mkdir(parents=True, exist_ok=True)
            
            # 生成保存文件名
            save_file_name = self.make_save_file_name(content_id, image_url)
            
            # 下载图片
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(image_url, headers={"User-Agent": utils.get_user_agent()})
                response.raise_for_status()
                
                # 保存图片
                async with aiofiles.open(save_file_name, 'wb') as f:
                    await f.write(response.content)
                    utils.logger.info(f"[ZhihuImage.save_image] save image {save_file_name} success ...")
        except Exception as e:
            utils.logger.error(f"[ZhihuImage.save_image] save image failed: {e}")

    async def batch_store_images(self, content_id: str, image_urls: List[str]):
        """
        批量保存图片
        Args:
            content_id: 内容ID
            image_urls: 图片URL列表
        """
        if not image_urls:
            return
        
        tasks = []
        for image_url in image_urls:
            task = self.save_image(content_id, image_url)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
