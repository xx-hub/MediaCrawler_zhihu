# -*- coding: utf-8 -*-
"""
analyze: 知乎回答思维逻辑分析。

迁移自根目录 analyze_thinking_logic.py,增强:
- 路径参数化(--md-dir / --output-dir / --author)
- 统计前剔除 Markdown 图片语法与占位符(修复"图片"污染高频词的问题)
- 结果输出:分析报告 Markdown + 原始数据 JSON
"""
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .common import default_analysis_dir, strip_image_markdown

# ---------------------------------------------------------------------------
# 常量与停用词
# ---------------------------------------------------------------------------
STOPWORDS = {
    '的', '了', '是', '在', '和', '就', '不', '人', '有', '都', '一',
    '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    '没', '看', '好', '自己', '这', '他', '她', '它', '们', '那', '些',
    '吗', '啊', '呢', '吧', '哦', '啦', '么', '我', '我们', '这个', '那个',
    '一个', '可以', '没有', '不是', '就是', '但是', '因为', '所以', '如果',
    '什么', '怎么', '如何', '为什么', '已经', '时候', '还是', '或者', '只是',
    '比较', '非常', '很多', '一些', '这种', '这样', '那样', '觉得', '知道',
    '可能', '需要', '之后', '之前', '然后', '关于', '还是', '其实', '虽然',
    '但是', '而且', '不过', '以及', '不是', '就是', '而是', '因为', '所以',
    '如果', '那么', '可以', '应该', '能够', '已经', '可能', '一样', '真的',
    '一点', '回事', '一下', '一直', '东西', '看到', '发现', '成为', '开始',
    '出来', '起来', '过来', '问题', '这里', '那里', '通过', '进行', '以及',
    '其中', '之间', '所谓', '甚至', '过去', '当时', '现在', '还是',
}

SIGNATURE_WORDS = [
    '吊诡', '悖论', '机制', '维度', '范式', '涌现', '嵌套',
    '折射', '映射', '张力', '弹性', '冗余', '收敛', '发散',
    '稳态', '脆弱', '韧性', '阈值', '相变', '熵增', '耦合',
    '博弈', '反馈', '迭代', '镜像', '解构', '祛魅', '规训',
    '异化', '遮蔽', '语境', '赋能', '杠杆', '锚定', '复利',
]

CONCEPT_DB = {
    '社会学': ['资本', '阶层', '制度', '话语', '权力', '身份', '场域', '规训',
                '异化', '工具理性', '结构', '规范', '角色', '生态位'],
    '物理学': ['场', '波', '惯性', '热力学', '引力', '势能', '动能', '摩擦',
                '量子', '相对论', '熵', '熵增', '相变', '临界点', '共振', '阻尼', '压强', '张力', '能量'],
    '经济学': ['博弈', '垄断', '杠杆', '定价权', '铸币权', '复利', '地租',
                '边际', '套利', '对冲', '稀缺', '交易成本', '外部性', '信息不对称'],
    '生物学': ['基因', '进化', '自然选择', '物种', 'DNA', '繁衍', '变异',
                '免疫', '共生', '细胞', '神经', '神经元'],
    '数学/逻辑': ['概率', '分布', '收敛', '发散', '因果', '归谬', '反证',
                   '相关性', '全称量词', '必要不充分'],
    '认知科学': ['元认知', '认知偏差', '确认偏误', '锚定', '框架效应',
                  '工作记忆', '基底神经节', '前额叶', '多巴胺', '镜像神经元', '双加工'],
    '系统科学': ['反馈', '涌现', '自组织', '复杂系统', '网络效应', '混沌',
                  '稳态', '回路', '耦合', '层级', '递归'],
}

BODY_SECTION_RE = re.compile(r"## 回答内容\n(.*?)(?:\n---|\Z)", re.DOTALL)
YEAR_RE = re.compile(r"^(\d{4})")


def extract_body(filepath: Path) -> Optional[str]:
    """提取 `## 回答内容` 到 `---` 之间的纯作者输出,并剔除图片语法。"""
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    m = BODY_SECTION_RE.search(content)
    if not m:
        return None
    return strip_image_markdown(m.group(1).strip())


def analyze(
    md_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    author: str = "知乎回答",
) -> Dict:
    """
    对 md_dir 下的回答 Markdown 做思维逻辑分析,输出报告与原始数据。

    Args:
        md_dir: Markdown 目录,默认 data/zhihu/md
        output_dir: 输出目录,默认 data/zhihu/analysis
        author: 分析对象名称,用于报告标题

    Returns:
        原始分析数据 dict(同时写入 thinking_raw_data.json)
    """
    md_dir = Path(md_dir or default_analysis_dir().parent / "md")
    output_dir = Path(output_dir or default_analysis_dir())
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(f for f in md_dir.glob("*.md"))
    print(f"[analyze] 共发现 {len(files)} 个 MD 文件")

    # ---- 1. 基础元数据 ----
    year_counts: Counter = Counter()
    body_lengths: List[int] = []
    body_exist_count = 0

    for fname in files:
        m = YEAR_RE.match(fname.name)
        if m:
            year_counts[m.group(1)] += 1
        body = extract_body(fname)
        if body:
            body_exist_count += 1
            body_lengths.append(len(body))

    overall_avg_len = sum(body_lengths) / len(body_lengths) if body_lengths else 0
    sorted_lens = sorted(body_lengths)

    # ---- 2. 高频用词 ----
    word_counter: Counter = Counter()
    unique_articles_with_word: Counter = Counter()

    for fname in files:
        body = extract_body(fname)
        if not body:
            continue
        words = [w for w in re.findall(r'[\u4e00-\u9fff]{2,4}', body) if w not in STOPWORDS]
        for w in set(words):
            unique_articles_with_word[w] += 1
        for w in words:
            word_counter[w] += 1

    # ---- 3. 写作结构模式 ----
    structure_counts: Counter = Counter()
    for fname in files:
        body = extract_body(fname)
        if not body:
            continue
        if re.search(r'^\d+[\.\)、]', body, re.MULTILINE):
            structure_counts['数字编号分条'] += 1
        if re.search(r'[\u4e00-\u9fff]—[\u4e00-\u9fff]', body) or '→' in body or '->' in body:
            structure_counts['箭头/破折号推导链'] += 1
        if re.search(r'(比如|例如|举个例子|打个比方|就像一个|就像一个)', body):
            structure_counts['案例/类比论证'] += 1
        if re.search(r'(\*\*[^*]+\*\*)', body):
            structure_counts['加粗强调'] += 1
        if re.search(r'(第一点|第二点|第一层|第二层|第三层|第一方面|第二方面)', body):
            structure_counts['显式分层论述'] += 1
        if re.search(r'(爱因斯坦|达尔文|马克思|弗洛伊德|维特根斯坦|凯恩斯|哈耶克|福柯|韦伯|涂尔干|尼采|柏拉图|亚里士多德|康德|黑格尔|亚当斯密|卡尼曼|丹尼尔)', body):
            structure_counts['引用权威学者'] += 1
        if re.search(r'(研究[发现表明]|实验[发现表明]|数据显示|调查[发现表明]|论文|文献|期刊)', body):
            structure_counts['引用研究/数据'] += 1
        if re.search(r'(---|___|\*\*\*)', body):
            structure_counts['文内分隔线分段'] += 1
        if re.search(r'(更新|补充|追更|更一下|续更)|\d+赞了', body):
            structure_counts['追更/补充标记'] += 1
        if re.search(r'^[一二三四五六七八九十]、', body, re.MULTILINE):
            structure_counts['中文数字序号'] += 1

    # ---- 4. 核心思维框架 ----
    framework_counts: Counter = Counter()
    framework_patterns = {
        '概率/风险思维': r'(概率|可能性|风险|不确定|概率论|大概率|小概率)',
        '博弈/策略分析': r'(博弈|策略|最优|权衡|选择|取舍|博弈论)',
        '系统/反馈思维': r'(反馈|回路|循环|迭代|正反馈|负反馈|自强化)',
        '框架/模型思维': r'(框架|模型|范式|模式|结构)',
        '多维度分析': r'(维度|层面|视角|角度|层面)',
        '假设推演': r'(假设|假如|如果.*那么|如果.*就)',
        '机制原理解析': r'(机制|原理|底层逻辑|驱动力|动因)',
        '因果溯源': r'(因为|所以|原因|根源|根因|归因)',
        '概念重定义': r'(定义|所谓|本质|实质|说白了)',
        '边界/条件思维': r'(边界|临界|门槛|阈值|上限|下限|瓶颈)',
        '对比分析': r'(对比|相比|区别|差异|不同)',
        '演化/历史视角': r'(演化|进化|演变|变迁|历史|从.*到)',
        '分层/结构思维': r'(底层|上层|金字塔|分层|层级|结构)',
        '趋势预判': r'(趋势|方向|走向|未来|预测|预判)',
        '成本收益分析': r'(成本|收益|投入产出|性价比|效率)',
    }
    for fname in files:
        body = extract_body(fname)
        if not body:
            continue
        for framework, pattern in framework_patterns.items():
            if re.search(pattern, body):
                framework_counts[framework] += 1

    # ---- 5. 论证句式 ----
    sentence_counts: Counter = Counter()
    sentence_patterns = {
        '否定-肯定对比（不是A而是B）': r'(不是.*而是|不在于.*在于|重要的不是)',
        '递进序列（从A到B再到C）': r'(从.*到.*再到|从.*走向|从.*进入)',
        '本质揭示句（归根结底）': r'(本质上|归根结底|说到底|骨子里|说白了)',
        '反常揭示句（有趣的是）': r'(有趣的是|吊诡的是|讽刺的是|悖论的是|耐人寻味)',
        '实用建议句（不妨/建议）': r'(不妨|建议|值得尝试|推荐|可以试试)',
        '举例引导句': r'(举个例|比如说|打个比方)',
        '强调提醒句': r'(请注意|值得注意|重要的是|关键在)',
        '换述解释句': r'(换句话说|换言之|也就是说|即)',
        '反驳立场句': r'(我不认为|我反对|我质疑|我不认同|恰恰相反)',
        '第一人称断言': r'(让我\w{1,3}|我\w{0,2}说|我\w{0,2}讲|我\w{0,2}认为)',
    }
    for fname in files:
        body = extract_body(fname)
        if not body:
            continue
        for name, pattern in sentence_patterns.items():
            if re.search(pattern, body):
                sentence_counts[name] += 1

    # ---- 6. 跨学科知识迁移 ----
    domain_total: Counter = Counter()
    concept_detail: Counter = Counter()
    for fname in files:
        body = extract_body(fname)
        if not body:
            continue
        for domain, concepts in CONCEPT_DB.items():
            for c in concepts:
                if c in body:
                    concept_detail[f'{domain} · {c}'] += 1
                    domain_total[domain] += 1

    # ---- 7. 论证深度 ----
    long_articles = sum(1 for n in body_lengths if n > 3000)
    medium_articles = sum(1 for n in body_lengths if 1000 < n <= 3000)
    short_articles = sum(1 for n in body_lengths if 200 < n <= 1000)
    very_short = sum(1 for n in body_lengths if n <= 200)

    # ---- 8. 风格词 ----
    style_words = []
    for word, count in word_counter.most_common(200):
        article_ratio = unique_articles_with_word[word] / body_exist_count * 100 if body_exist_count else 0
        if article_ratio >= 5:
            style_words.append((word, count, unique_articles_with_word[word], article_ratio))

    # ---- 报告 ----
    def pct(count: int) -> float:
        return count / body_exist_count * 100 if body_exist_count else 0.0

    report_lines: List[str] = []
    report_lines.append(f'# {author}思维逻辑分析报告（纯回答内容）')
    report_lines.append('')
    report_lines.append(f'分析时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    report_lines.append(f'分析范围：{len(files)} 篇知乎回答，成功提取 {body_exist_count} 篇正文')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## 一、创作基础数据')
    report_lines.append('')
    report_lines.append(f'- 总文章数：{len(files)} 篇')
    report_lines.append(f'- 成功提取正文：{body_exist_count} 篇')
    if year_counts:
        report_lines.append(f'- 创作跨度：{min(year_counts.keys())} 年 - {max(year_counts.keys())} 年')
    if body_lengths:
        report_lines.append(f'- 平均回答长度：{overall_avg_len:.0f} 字符')
        report_lines.append(f'- 最长回答：{max(body_lengths)} 字符')
        report_lines.append(f'- 中位数长度：{sorted_lens[len(sorted_lens)//2]} 字符')
    report_lines.append('')
    report_lines.append('### 年度分布')
    for year in sorted(year_counts.keys()):
        bar = '█' * (year_counts[year] // 50 + 1)
        report_lines.append(f'- {year}: {year_counts[year]} 篇 {bar}')
    if body_lengths:
        report_lines.append('')
        report_lines.append('### 论证深度')
        report_lines.append(f'- 长篇(>3000字): {long_articles} ({pct(long_articles):.1f}%)')
        report_lines.append(f'- 中篇(1000-3000): {medium_articles} ({pct(medium_articles):.1f}%)')
        report_lines.append(f'- 短篇(200-1000): {short_articles} ({pct(short_articles):.1f}%)')
        report_lines.append(f'- 极短(<200字): {very_short} ({pct(very_short):.1f}%)')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## 二、高频用词体系（Top 60）')
    report_lines.append('')
    report_lines.append('| 关键词 | 总频次 | 覆盖文章数 | 覆盖率 |')
    report_lines.append('|--------|--------|-----------|-------|')
    for word, count in word_counter.most_common(60):
        art = unique_articles_with_word[word]
        report_lines.append(f'| {word} | {count} | {art} | {pct(art):.1f}% |')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## 三、写作结构模式')
    report_lines.append('')
    report_lines.append('| 结构特征 | 出现篇数 | 占比 |')
    report_lines.append('|---------|---------|------|')
    for pattern, count in structure_counts.most_common():
        report_lines.append(f'| {pattern} | {count} | {pct(count):.1f}% |')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## 四、核心思维框架')
    report_lines.append('')
    report_lines.append('| 思维框架 | 出现篇数 | 占比 |')
    report_lines.append('|---------|---------|------|')
    for framework, count in framework_counts.most_common():
        report_lines.append(f'| {framework} | {count} | {pct(count):.1f}% |')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## 五、论证句式偏好')
    report_lines.append('')
    report_lines.append('| 句式类型 | 出现篇数 | 占比 |')
    report_lines.append('|---------|---------|------|')
    for pattern, count in sentence_counts.most_common():
        report_lines.append(f'| {pattern} | {count} | {pct(count):.1f}% |')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## 六、跨学科知识迁移')
    report_lines.append('')
    report_lines.append('### 学科领域引用总量')
    for domain, count in sorted(domain_total.items(), key=lambda x: -x[1]):
        report_lines.append(f'- **{domain}**: {count} 次引用')
    report_lines.append('')
    report_lines.append('### Top 30 跨学科概念')
    report_lines.append('')
    report_lines.append('| 概念 | 出现次数 |')
    report_lines.append('|------|---------|')
    for concept, count in concept_detail.most_common(30):
        report_lines.append(f'| {concept} | {count} |')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## 七、标志性个人风格词')
    report_lines.append('')
    report_lines.append('| 词汇 | 覆盖文章数 | 覆盖率 |')
    report_lines.append('|------|-----------|-------|')
    for word in SIGNATURE_WORDS:
        count = unique_articles_with_word[word]
        report_lines.append(f'| {word} | {count} | {pct(count):.1f}% |')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## 八、高覆盖率核心词（Top 30）')
    report_lines.append('')
    report_lines.append('| 词汇 | 总计频次 | 覆盖文章数 | 覆盖率 |')
    report_lines.append('|------|---------|-----------|-------|')
    for word, total_count, articles, ratio in style_words[:30]:
        report_lines.append(f'| {word} | {total_count} | {articles} | {ratio:.1f}% |')

    report_path = output_dir / 'thinking_logic_report.md'
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')
    print(f"[analyze] 报告已生成: {report_path}")

    raw_data: Dict = {
        'total_files': len(files),
        'body_extracted': body_exist_count,
        'year_distribution': dict(year_counts.most_common()),
        'body_length_stats': {
            'avg': round(overall_avg_len, 0),
            'max': max(body_lengths) if body_lengths else 0,
            'min': min(body_lengths) if body_lengths else 0,
            'median': sorted_lens[len(sorted_lens)//2] if sorted_lens else 0,
        },
        'top_words': [{'word': w, 'count': c, 'articles': unique_articles_with_word[w],
                        'coverage': round(pct(unique_articles_with_word[w]), 1)}
                      for w, c in word_counter.most_common(100)],
        'structure_patterns': {k: v for k, v in structure_counts.most_common()},
        'framework_patterns': {k: v for k, v in framework_counts.most_common()},
        'sentence_patterns': {k: v for k, v in sentence_counts.most_common()},
        'cross_domain': {k: v for k, v in concept_detail.most_common(60)},
        'signature_words': {w: unique_articles_with_word[w] for w in SIGNATURE_WORDS},
    }

    raw_path = output_dir / 'thinking_raw_data.json'
    raw_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[analyze] 原始数据已保存: {raw_path}")
    print("[analyze] 分析完成!")
    return raw_data
