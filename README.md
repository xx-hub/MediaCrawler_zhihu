# 🔥 MediaCrawler_zhihu 创作者分身创建助手 🕷️

<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/xx-hub/MediaCrawler_zhihu?style=social)](https://github.com/xx-hub/MediaCrawler_zhihu/stargazers)
[![License](https://img.shields.io/github/license/xx-hub/MediaCrawler_zhihu)](https://github.com/xx-hub/MediaCrawler_zhihu/blob/main/LICENSE)
[![中文](https://img.shields.io/badge/🇨🇳_中文-当前-blue)](README.md)

</div>

> **免责声明：**
>
> 大家请以学习为目的使用本仓库⚠️⚠️⚠️⚠️，[爬虫违法违规的案件](https://github.com/HiddenStrawberry/Crawler_Illegal_Cases_In_China)  <br>
>
> 本仓库的所有内容仅供学习和参考之用，禁止用于商业用途。任何人或组织不得将本仓库的内容用于非法用途或侵犯他人合法权益。本仓库所涉及的爬虫技术仅用于学习和研究，不得用于对其他平台进行大规模爬虫或其他非法行为。对于因使用本仓库内容而引起的任何法律责任，本仓库不承担任何责任。使用本仓库的内容即表示您同意本免责声明的所有条款和条件。

## 📖 项目简介

基于 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 修改的知乎用户本人回答采集。

### 🎯 主要功能

- ✅ **创作者主页爬取** - 获取知乎用户的所有回答，用于创建创作者分身的LLM微调数据集。

## 🚀 快速开始

### 📋 前置依赖

#### 1. Python 环境

需要 Python 3.8 或更高版本。

#### 2. Node.js

项目依赖 Node.js 环境（用于知乎签名算法）：

- **下载地址**：<https://nodejs.org/en/download/>
- **版本要求**：>= 16.0.0

验证安装：

```bash
node --version
```

### 📦 安装步骤

```bash
# 克隆项目
git clone https://github.com/xx-hub/MediaCrawler_zhihu.git
```

#### 方法 1：使用 uv（推荐）

```bash
# 进入项目目录
cd MediaCrawler_zhihu

# 安装 uv（如果还没安装）
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/mac: curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync

# 安装浏览器驱动
uv run playwright install
```

#### 方法 2：使用 venv

```bash
# 进入项目目录
cd MediaCrawler_zhihu

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows: venv\Scripts\activate
# Linux/mac: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装浏览器驱动
playwright install
```

## ⚙️ 配置说明

在运行爬虫前，需要新建并修改配置文件。

### 1. 基础配置 (config/base_config.py)（复制config/base_config.example.py后改名为base_config.py）

```python
# 平台选择
PLATFORM = "zhihu"

# 登录方式
LOGIN_TYPE = "qrcode"  # qrcode(扫码) | phone(手机) | cookie(cookie)

# 爬取类型
CRAWLER_TYPE = "creator"  # search(搜索) | detail(指定) | creator(创作者)

# 数据保存方式
SAVE_DATA_OPTION = "json"  # json | csv | db | sqlite | excel

# 是否启用 CDP 模式（使用现有浏览器）
ENABLE_CDP_MODE = True

# 是否显示浏览器窗口
HEADLESS = False
```

### 2. 知乎配置 (config/zhihu_config.py)（复制config/zhihu_config.example.py后改名为zhihu_config.py）

```python
# 要爬取的创作者主页 URL 列表
ZHIHU_CREATOR_URL_LIST = [
    "https://www.zhihu.com/people/example_user",#修改为自己的主页
    ]


```

## 🎮 使用方法

### 1. 爬取创作者的所有回答

```bash
# 方法 1：使用命令行参数
uv run main.py --platform zhihu --lt qrcode --type creator

# 方法 2：直接运行
uv run main.py
```

程序会：

1. 打开浏览器
2. 显示二维码登录页面
3. 用手机知乎 APP 扫码登录
4. 自动爬取配置文件中创作者的所有回答（支持断点续传，中断后从上次分页游标继续）

### 2. 数据后处理（统一工具链）

运行结束后，用 `tools/zhihu_export` 工具包处理数据：

```bash
# 合并所有 JSON 快照并导出为 Markdown（按 content_id 增量去重，建议先试跑）
uv run python -m tools.zhihu_export.cli export-md --merge --limit 20

# 按作者导出（推荐，每个创作者一个目录）
uv run python -m tools.zhihu_export.cli export-md --merge --nickname 你的知乎昵称 --output data/zhihu/md-你的昵称

# 导出 OpenAI 微调数据集（ChatML，问题标题+描述作为 user，回答作为 assistant）
uv run python -m tools.zhihu_export.cli export-jsonl --merge

# 质量过滤：只保留 >=100 字且赞同 >=10 的回答
uv run python -m tools.zhihu_export.cli export-jsonl --merge --min-length 100 --min-votes 10

# 按 content_id 去重
uv run python -m tools.zhihu_export.cli dedupe --input data/zhihu/json/creator_contents_YYYY-MM-DD.json

# 思维逻辑分析（统计用词体系、论证结构、跨学科概念，生成报告）
uv run python -m tools.zhihu_export.cli analyze --md-dir data/zhihu/md-你的昵称 --author 你的昵称

# 仅合并快照（增量合并多次爬取的结果）
uv run python -m tools.zhihu_export.cli merge
```

## 💾 数据保存

爬取的数据保存在 `data/zhihu/` 目录下：

```
data/
├── zhihu/
│   ├── json/                    # JSON 格式数据
│   │   ├── creator_contents_YYYYMMDD.json  # 创作者内容（每次爬取一个快照）
│   │   └── creator_creators_YYYYMMDD.json  # 创作者信息
│   ├── md-昵称/                 # Markdown 格式（export-md 产出，每个回答一个文件）
│   ├── analysis/                # 思维逻辑分析报告（analyze 产出）
│   └── progress_creator.json    # 断点续传进度（page_offset = 分页游标）
└── jsonl/                      # 用于LLM微调的jsonl格式数据（export-jsonl 产出）
```

其他信息请参考 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 项目。

## 📚 参考资料

- [MediaCrawler 原项目](https://github.com/NanmiCoder/MediaCrawler)

**享受复刻自己的乐趣！🕷️**
