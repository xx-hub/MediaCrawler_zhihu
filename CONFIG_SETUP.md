# 配置文件设置说明

本项目使用示例配置文件（`.example.py`）来保护个人隐私信息。请按照以下步骤设置配置文件。

## 快速开始

### 1. 复制示例配置文件

在 `config/` 目录下，将所有 `.example.py` 文件复制为对应的配置文件：

```bash
# Windows (PowerShell)
cd config
copy base_config.example.py base_config.py
copy zhihu_config.example.py zhihu_config.py
copy xhs_config.example.py xhs_config.py
copy dy_config.example.py dy_config.py
copy ks_config.example.py ks_config.py
copy bilibili_config.example.py bilibili_config.py
copy weibo_config.example.py weibo_config.py
copy tieba_config.example.py tieba_config.py

# Linux / macOS
cd config
cp base_config.example.py base_config.py
cp zhihu_config.example.py zhihu_config.py
cp xhs_config.example.py xhs_config.py
cp dy_config.example.py dy_config.py
cp ks_config.example.py ks_config.py
cp bilibili_config.example.py bilibili_config.py
cp weibo_config.example.py weibo_config.py
cp tieba_config.example.py tieba_config.py
```

### 2. 修改配置文件

根据您的需求修改配置文件中的参数：

#### `config/base_config.py`

主要配置项：

```python
# 平台选择：xhs | dy | ks | bili | wb | tieba | zhihu
PLATFORM = "zhihu"

# 搜索关键词（多个关键词用英文逗号分隔）
KEYWORDS = "Python,爬虫,数据分析"

# 登录方式：qrcode | phone | cookie
LOGIN_TYPE = "qrcode"

# 爬取类型：search | detail | creator
CRAWLER_TYPE = "creator"

# 数据保存方式：csv | db | json | sqlite | excel
SAVE_DATA_OPTION = "json"

# 是否启用无头模式（不显示浏览器窗口）
HEADLESS = False

# 是否启用 CDP 模式（使用本地 Chrome/Edge 浏览器）
ENABLE_CDP_MODE = True
```

#### `config/zhihu_config.py`

知乎平台特定配置：

```python
# 要爬取的知乎用户主页URL列表
ZHIHU_CREATOR_URL_LIST = [
    "https://www.zhihu.com/people/example_user",
]

# 要爬取的特定知乎内容ID列表（回答、文章、视频）
ZHIHU_SPECIFIED_ID_LIST = [
    "https://www.zhihu.com/question/xxxxxxxxx/answer/xxxxxxxxx",
    "https://zhuanlan.zhihu.com/p/xxxxxxxxx",
    "https://www.zhihu.com/zvideo/xxxxxxxxx",
]
```

### 3. 运行爬虫

配置完成后，运行爬虫：

```bash
# 使用 uv（推荐）
uv run main.py

# 或使用 Python
python main.py
```

## 配置文件说明

| 配置文件 | 说明 | 是否必需 |
|---------|------|---------|
| `base_config.py` | 基础配置文件，包含所有平台通用配置 | ✅ 必需 |
| `zhihu_config.py` | 知乎平台配置 | 知乎平台必需 |
| `xhs_config.py` | 小红书平台配置 | 小红书平台必需 |
| `dy_config.py` | 抖音平台配置 | 抖音平台必需 |
| `ks_config.py` | 快手平台配置 | 快手平台必需 |
| `bilibili_config.py` | B站平台配置 | B站平台必需 |
| `weibo_config.py` | 微博平台配置 | 微博平台必需 |
| `tieba_config.py` | 贴吧平台配置 | 贴吧平台必需 |

## 隐私保护

- **不要将包含个人信息的配置文件提交到 Git 仓库**
- `.gitignore` 已配置忽略 `config/*.py` 文件（除了 `.example.py`）
- 如果需要分享配置，请使用 `.example.py` 作为模板
- Cookie、手机号等敏感信息请妥善保管

## 常见问题

### Q: 配置文件被 .gitignore 忽略了，如何提交初始配置？

A: 在本地开发时保留您的个人配置文件。如果要为项目提供默认配置，请修改 `.example.py` 文件并提交这些文件。

### Q: 如何在不同环境使用不同配置？

A: 可以创建多个配置文件副本（如 `config_dev.py`, `config_prod.py`），然后在运行时指定使用哪个配置。

### Q: Cookie 在哪里获取？

A: 使用 `--lt cookie` 参数，然后在浏览器登录后，通过开发者工具获取 Cookie 字符串。

## 更多帮助

- 查看 [README.md](./README.md) 了解项目使用方法
- 查看 [config/](./config/) 目录下的示例配置文件获取详细配置选项
- 提交 Issue 报告配置相关问题
