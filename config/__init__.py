# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/config/__init__.py
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


import importlib.util
from pathlib import Path


_CONFIG_DIR = Path(__file__).parent


def _load_config_file(filename: str) -> None:
    """从 config 目录加载配置文件,把其公有属性注入当前命名空间。

    用于模板化配置(如 base_config.example.py)的优雅降级:
    真实配置文件未复制时,回退到 example 占位值,保证仓库克隆后开箱即用。
    """
    file_path = _CONFIG_DIR / filename
    if not file_path.exists():
        return
    spec = importlib.util.spec_from_file_location(f"config.{Path(filename).stem}", file_path)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    # 设置父包,使文件内 `from .xxx_config import *` 相对导入可解析为 config.xxx_config
    module.__package__ = "config"
    spec.loader.exec_module(module)
    for _name in dir(module):
        if not _name.startswith("_"):
            globals()[_name] = getattr(module, _name)


# 优先加载真实配置;缺失时回退到 example 模板(占位值)并提示
# 按 CONFIG_SETUP.md 复制模板即可获得可编辑的真实配置
try:
    from .base_config import *  # type: ignore[import-not-found]
except ModuleNotFoundError:
    import logging
    logging.getLogger(__name__).warning(
        "config/base_config.py 不存在,已回退到 base_config.example.py 占位配置;"
        "请按 CONFIG_SETUP.md 复制模板后编辑。"
    )
    _load_config_file("base_config.example.py")
from .db_config import *
