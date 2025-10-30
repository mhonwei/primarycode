"""
案例生成器 - 基于搜索结果生成AI教学案例
"""
import json
from datetime import datetime


class CaseGenerator:
    """AI教学案例生成器"""

    def __init__(self):
        self.case_templates = {
            'problem': self._generate_problem_based_case,
            'project': self._generate_project_based_case,
            'discussion': self._generate_discussion_based_case
        }

    def generate(self, keyword, source_data, case_type='problem',
                 difficulty='intermediate', focus='theory',
                 audience='undergraduate', word_limit=1000):
        """
        生成教学案例
        :param keyword: 关键词
        :param source_data: 源数据（搜索结果）
        :param case_type: 案例类型
        :param difficulty: 难度等级
        :param focus: 内容侧重点
        :param audience: 目标受众
        :param word_limit: 字数限制
        :return: 生成的案例
        """
        generator_func = self.case_templates.get(case_type, self._generate_problem_based_case)

        case = generator_func(
            keyword=keyword,
            source_data=source_data,
            difficulty=difficulty,
            focus=focus,
            audience=audience,
            word_limit=word_limit
        )

        # 添加元数据
        case['metadata'] = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'keyword': keyword,
            'case_type': case_type,
            'difficulty': difficulty,
            'focus': focus,
            'audience': audience,
            'estimated_reading_time': self._estimate_reading_time(case)
        }

        return case

    def _generate_problem_based_case(self, keyword, source_data, difficulty, focus, audience, word_limit):
        """生成问题导向型案例"""

        # 提取关键信息
        papers = source_data.get('papers', [])
        tech = source_data.get('tech', [])
        products = source_data.get('products', [])
        industry = source_data.get('industry', [])
        trends = source_data.get('trends', [])

        # 构建案例
        case = {
            'title': f'如何利用{keyword}解决实际问题？',
            'case_type': '问题导向型',
            'difficulty_level': self._get_difficulty_label(difficulty),
            'target_audience': self._get_audience_label(audience),

            'background': self._generate_background(keyword, industry, trends, focus),
            'problem_statement': self._generate_problem_statement(keyword, difficulty, focus),
            'learning_objectives': self._generate_learning_objectives(keyword, difficulty, audience),

            'technical_foundation': self._generate_technical_foundation(keyword, papers, tech, focus),
            'case_analysis': self._generate_case_analysis(keyword, industry, products, focus),

            'solution_approach': self._generate_solution_approach(keyword, tech, difficulty),
            'implementation_details': self._generate_implementation(keyword, tech, difficulty),

            'discussion_questions': self._generate_discussion_questions(keyword, focus, difficulty),
            'further_reading': self._generate_references(papers, tech, industry),

            'assessment': self._generate_assessment(keyword, difficulty, audience),
            'teaching_tips': self._generate_teaching_tips(keyword, case_type='problem', audience=audience)
        }

        return case

    def _generate_project_based_case(self, keyword, source_data, difficulty, focus, audience, word_limit):
        """生成项目驱动型案例"""

        papers = source_data.get('papers', [])
        tech = source_data.get('tech', [])
        products = source_data.get('products', [])

        case = {
            'title': f'{keyword}实战项目：从理论到应用',
            'case_type': '项目驱动型',
            'difficulty_level': self._get_difficulty_label(difficulty),
            'target_audience': self._get_audience_label(audience),

            'project_overview': f'本项目旨在通过实践{keyword}技术，构建一个完整的应用系统，帮助学习者掌握从理论到实践的完整流程。',

            'project_objectives': [
                f'理解{keyword}的核心原理和技术架构',
                f'掌握{keyword}的实现方法和工具使用',
                f'能够独立设计和开发{keyword}应用',
                '培养问题分析和解决能力'
            ],

            'prerequisites': self._generate_prerequisites(difficulty, audience),

            'project_phases': [
                {
                    'phase': '第一阶段：需求分析与系统设计',
                    'duration': '1-2周',
                    'tasks': [
                        '分析项目需求和目标用户',
                        '设计系统架构和技术方案',
                        '制定项目计划和时间表'
                    ],
                    'deliverables': ['需求文档', '系统设计文档', '项目计划']
                },
                {
                    'phase': f'第二阶段：{keyword}模型开发',
                    'duration': '2-3周',
                    'tasks': [
                        '数据收集和预处理',
                        '模型选择和训练',
                        '模型评估和优化'
                    ],
                    'deliverables': ['训练好的模型', '性能评估报告']
                },
                {
                    'phase': '第三阶段：系统集成与测试',
                    'duration': '1-2周',
                    'tasks': [
                        '开发用户界面',
                        '集成模型和应用',
                        '系统测试和调优'
                    ],
                    'deliverables': ['完整应用系统', '测试报告']
                },
                {
                    'phase': '第四阶段：部署与展示',
                    'duration': '1周',
                    'tasks': [
                        '系统部署上线',
                        '准备项目展示',
                        '撰写项目总结'
                    ],
                    'deliverables': ['上线系统', '项目展示PPT', '总结报告']
                }
            ],

            'technical_stack': self._generate_tech_stack(tech),
            'resources': self._generate_project_resources(papers, tech),

            'evaluation_criteria': [
                '技术实现的完整性和正确性（40%）',
                '系统功能和用户体验（30%）',
                '创新性和实用性（20%）',
                '文档和展示质量（10%）'
            ],

            'common_challenges': self._generate_challenges(keyword, difficulty),
            'teaching_tips': self._generate_teaching_tips(keyword, case_type='project', audience=audience)
        }

        return case

    def _generate_discussion_based_case(self, keyword, source_data, difficulty, focus, audience, word_limit):
        """生成讨论型案例"""

        trends = source_data.get('trends', [])
        industry = source_data.get('industry', [])
        products = source_data.get('products', [])

        case = {
            'title': f'{keyword}：技术、伦理与社会影响',
            'case_type': '讨论型',
            'difficulty_level': self._get_difficulty_label(difficulty),
            'target_audience': self._get_audience_label(audience),

            'case_overview': f'本案例通过分析{keyword}的发展现状和应用实践，引导学生思考技术创新与社会责任的平衡，培养批判性思维。',

            'background_story': self._generate_discussion_background(keyword, trends, industry),

            'key_stakeholders': [
                {'role': '技术开发者', 'perspective': '追求技术创新和性能突破'},
                {'role': '企业管理者', 'perspective': '关注商业价值和投资回报'},
                {'role': '普通用户', 'perspective': '关心隐私保护和使用体验'},
                {'role': '政策制定者', 'perspective': '平衡创新发展和风险管控'},
                {'role': '伦理学家', 'perspective': '关注技术伦理和社会影响'}
            ],

            'core_issues': self._generate_core_issues(keyword, focus),

            'discussion_scenarios': [
                {
                    'scenario': f'{keyword}在招聘中的应用',
                    'description': f'某公司使用{keyword}系统筛选简历和评估候选人，提高了效率但引发公平性争议。',
                    'questions': [
                        f'{keyword}招聘系统可能存在哪些偏见？',
                        '如何确保算法的公平性和透明度？',
                        '人类判断和AI判断应如何平衡？'
                    ]
                },
                {
                    'scenario': f'{keyword}与隐私保护',
                    'description': f'{keyword}系统需要大量数据训练，但可能涉及用户隐私问题。',
                    'questions': [
                        '如何在数据利用和隐私保护之间取得平衡？',
                        '用户是否应该拥有数据的控制权？',
                        '企业应承担什么样的责任？'
                    ]
                },
                {
                    'scenario': f'{keyword}的社会影响',
                    'description': f'{keyword}技术可能导致某些工作岗位消失，同时创造新的机会。',
                    'questions': [
                        '技术进步与就业的关系如何处理？',
                        '社会应如何帮助受影响的群体？',
                        '教育体系需要做出哪些调整？'
                    ]
                }
            ],

            'discussion_framework': {
                '技术层面': ['技术可行性', '性能指标', '实现难度'],
                '商业层面': ['市场需求', '成本收益', '竞争优势'],
                '伦理层面': ['公平性', '透明性', '责任归属'],
                '社会层面': ['就业影响', '教育变革', '法律监管']
            },

            'case_analysis_guide': self._generate_analysis_guide(keyword),

            'recommended_readings': self._generate_discussion_readings(trends, industry),

            'assessment_rubric': {
                '参与度': '积极参与讨论，提出有见地的观点',
                '批判性思维': '能够从多角度分析问题',
                '论证能力': '观点有充分的论据支持',
                '团队协作': '尊重他人意见，善于合作'
            },

            'teaching_tips': self._generate_teaching_tips(keyword, case_type='discussion', audience=audience)
        }

        return case

    def _generate_background(self, keyword, industry, trends, focus):
        """生成背景介绍"""
        background = f"""
随着人工智能技术的快速发展，{keyword}已经成为当前最受关注的技术领域之一。

**技术发展现状**
{keyword}技术在近年来取得了显著进展，特别是在算法优化、模型架构和应用场景方面。
许多研究机构和企业都在积极探索{keyword}的创新应用。

**行业应用情况**
"""
        if industry:
            app = industry[0]
            background += f"{app['industry']}等行业已经开始大规模应用{keyword}技术，取得了显著成效。"
        else:
            background += f"多个行业正在探索{keyword}的应用潜力，包括医疗、金融、教育等领域。"

        background += f"""

**发展趋势**
从技术发展趋势来看，{keyword}正朝着更加智能化、自动化的方向发展，
同时也面临着数据隐私、算法偏见等挑战。
"""

        return background.strip()

    def _generate_problem_statement(self, keyword, difficulty, focus):
        """生成问题陈述"""
        if difficulty == 'beginner':
            return f"如何理解{keyword}的基本概念和工作原理？在简单场景下如何应用{keyword}技术？"
        elif difficulty == 'intermediate':
            return f"在复杂的实际场景中，如何设计和实现基于{keyword}的解决方案？如何评估和优化系统性能？"
        else:  # advanced
            return f"面对{keyword}领域的前沿挑战，如何进行创新性研究？如何平衡技术性能、成本和伦理考量？"

    def _generate_learning_objectives(self, keyword, difficulty, audience):
        """生成学习目标"""
        objectives = [
            f"理解{keyword}的核心概念和技术原理",
            f"掌握{keyword}的实现方法和常用工具",
            f"能够分析{keyword}在实际场景中的应用",
            "培养问题分析和解决能力"
        ]

        if difficulty == 'advanced':
            objectives.append(f"能够进行{keyword}领域的创新性研究")
            objectives.append("理解技术发展的伦理和社会影响")

        return objectives

    def _generate_technical_foundation(self, keyword, papers, tech, focus):
        """生成技术基础部分"""
        foundation = f"""
**核心技术**
{keyword}技术的实现基于多个关键技术组件：

1. **算法原理**:
   - 主要算法和模型架构
   - 训练和优化方法
   - 性能评估指标

2. **技术栈**:
"""
        if tech:
            t = tech[0]
            foundation += f"   - {t['title']}: {t['description']}\n"
            if t.get('language'):
                foundation += f"   - 主要使用 {t['language']} 语言实现\n"
        else:
            foundation += "   - Python 深度学习框架 (TensorFlow/PyTorch)\n"
            foundation += "   - 数据处理工具\n"
            foundation += "   - 模型部署平台\n"

        foundation += """
3. **最新研究进展**:
"""
        if papers:
            paper = papers[0]
            foundation += f"   - {paper['title']}\n"
            foundation += f"   - 研究要点: {paper['summary'][:150]}...\n"
        else:
            foundation += f"   - {keyword}领域持续有新的研究成果发布\n"
            foundation += "   - 建议关注顶级会议和期刊\n"

        return foundation.strip()

    def _generate_case_analysis(self, keyword, industry, products, focus):
        """生成案例分析"""
        analysis = f"**实际应用案例**\n\n"

        if industry:
            app = industry[0]
            analysis += f"**案例: {app['title']}**\n\n"
            analysis += f"- 实施单位: {app['company']}\n"
            analysis += f"- 应用场景: {app['description']}\n"
            analysis += f"- 实施方案: {app['implementation']}\n"
            analysis += f"- 取得成效: {', '.join(app['benefits'][:2])}\n"
            analysis += f"- 面临挑战: {', '.join(app['challenges'][:2])}\n"
        else:
            analysis += f"{keyword}技术在实际应用中展现出巨大潜力，\n"
            analysis += "但同时也需要解决数据质量、模型可解释性等问题。\n"

        return analysis.strip()

    def _generate_solution_approach(self, keyword, tech, difficulty):
        """生成解决方案"""
        solution = f"""
**解决方案设计**

1. **问题分析**
   - 明确问题定义和目标
   - 分析数据可用性和质量
   - 评估技术可行性

2. **方案设计**
   - 选择合适的{keyword}模型和算法
   - 设计系统架构
   - 制定实施计划

3. **实施步骤**
   - 数据准备和预处理
   - 模型训练和验证
   - 系统集成和测试
   - 部署和监控

4. **质量保证**
   - 建立性能评估标准
   - 持续监控和优化
   - 风险管理和应对
"""
        return solution.strip()

    def _generate_implementation(self, keyword, tech, difficulty):
        """生成实施细节"""
        if difficulty == 'beginner':
            return f"""
**基础实现示例**

使用Python和常用深度学习框架，可以快速实现{keyword}的基本功能：

```python
# 1. 数据准备
import numpy as np
import tensorflow as tf

# 加载和预处理数据
data = load_data()
processed_data = preprocess(data)

# 2. 模型构建
model = build_model()

# 3. 训练模型
model.fit(processed_data)

# 4. 评估和预测
results = model.evaluate(test_data)
predictions = model.predict(new_data)
```

关键要点：
- 数据质量直接影响模型性能
- 选择合适的模型架构
- 注意过拟合问题
"""
        else:
            return f"""
**高级实现要点**

1. **数据工程**
   - 大规模数据处理pipeline
   - 数据增强和平衡
   - 特征工程优化

2. **模型优化**
   - 超参数调优
   - 模型压缩和加速
   - 分布式训练

3. **工程化部署**
   - 模型服务化
   - 负载均衡和扩展
   - 监控和告警

4. **持续改进**
   - A/B测试
   - 用户反馈收集
   - 模型更新迭代
"""

    def _generate_discussion_questions(self, keyword, focus, difficulty):
        """生成讨论问题"""
        questions = []

        if focus == 'theory':
            questions.extend([
                f"{keyword}的核心技术原理是什么？",
                f"与传统方法相比，{keyword}有哪些优势和局限？",
                f"如何评估{keyword}系统的性能？"
            ])
        elif focus == 'business':
            questions.extend([
                f"{keyword}技术如何创造商业价值？",
                f"实施{keyword}项目的主要成本和风险是什么？",
                f"如何构建可持续的{keyword}商业模式？"
            ])
        elif focus == 'social':
            questions.extend([
                f"{keyword}对社会和就业的影响是什么？",
                f"如何确保{keyword}技术的公平性和包容性？",
                f"技术发展和社会责任如何平衡？"
            ])
        else:  # ethics
            questions.extend([
                f"{keyword}应用中存在哪些伦理问题？",
                f"如何建立{keyword}的伦理规范和监管机制？",
                f"开发者应该承担什么样的责任？"
            ])

        if difficulty == 'advanced':
            questions.append(f"{keyword}领域的未来研究方向是什么？")
            questions.append("如何推动产学研协同创新？")

        return questions

    def _generate_references(self, papers, tech, industry):
        """生成参考文献"""
        references = []

        if papers:
            for i, paper in enumerate(papers[:3], 1):
                references.append({
                    'type': '学术论文',
                    'title': paper['title'],
                    'authors': ', '.join(paper['authors'][:3]),
                    'link': paper['link'],
                    'year': paper['published'][:4] if paper['published'] else '2024'
                })

        if tech:
            for i, t in enumerate(tech[:2], 1):
                references.append({
                    'type': '技术资源',
                    'title': t['title'],
                    'description': t['description'],
                    'link': t['url']
                })

        if industry:
            app = industry[0]
            references.append({
                'type': '应用案例',
                'title': app['title'],
                'company': app['company'],
                'description': app['description']
            })

        return references

    def _generate_assessment(self, keyword, difficulty, audience):
        """生成评估标准"""
        assessment = {
            '知识掌握': f"能够准确理解和解释{keyword}的核心概念",
            '应用能力': f"能够将{keyword}技术应用于实际问题",
            '分析能力': "能够分析和评估不同方案的优劣",
            '创新思维': "能够提出创新性的想法和改进方案"
        }

        if difficulty == 'advanced':
            assessment['研究能力'] = "能够独立开展研究并获得有价值的成果"

        return assessment

    def _generate_teaching_tips(self, keyword, case_type, audience):
        """生成教学建议"""
        tips = []

        if case_type == 'problem':
            tips.extend([
                "引导学生从实际问题出发，理解技术的应用价值",
                "鼓励学生动手实践，而不仅是理论学习",
                "提供充分的案例和数据，帮助学生理解"
            ])
        elif case_type == 'project':
            tips.extend([
                "分组协作，培养团队合作能力",
                "设置阶段性检查点，及时反馈和指导",
                "鼓励创新，允许试错"
            ])
        else:  # discussion
            tips.extend([
                "创造开放包容的讨论氛围",
                "引导学生从多个角度思考问题",
                "平衡不同观点，避免偏见"
            ])

        if audience == 'undergraduate':
            tips.append("注重基础概念的讲解，避免过于复杂")
        elif audience == 'graduate':
            tips.append("深入探讨技术细节和前沿进展")
        else:  # professional
            tips.append("强调实践应用和业务价值")

        return tips

    def _generate_prerequisites(self, difficulty, audience):
        """生成先修知识"""
        prerequisites = []

        if difficulty == 'beginner':
            prerequisites = [
                'Python编程基础',
                '数据结构和算法基础',
                '线性代数和概率论基础'
            ]
        elif difficulty == 'intermediate':
            prerequisites = [
                'Python高级编程',
                '机器学习基础',
                '深度学习框架使用',
                '数据处理和可视化'
            ]
        else:  # advanced
            prerequisites = [
                '深度学习理论和实践',
                '分布式系统',
                '模型优化技术',
                '科研方法论'
            ]

        return prerequisites

    def _generate_tech_stack(self, tech):
        """生成技术栈"""
        stack = {
            '编程语言': ['Python 3.8+'],
            '深度学习框架': ['TensorFlow 2.x 或 PyTorch'],
            '数据处理': ['NumPy', 'Pandas', 'Scikit-learn'],
            '可视化工具': ['Matplotlib', 'Seaborn'],
            '开发工具': ['Jupyter Notebook', 'Git']
        }

        if tech:
            t = tech[0]
            if t.get('language'):
                if t['language'] not in stack['编程语言']:
                    stack['编程语言'].append(t['language'])

        return stack

    def _generate_project_resources(self, papers, tech):
        """生成项目资源"""
        resources = {
            '学习资料': [
                '官方文档和教程',
                '在线课程 (Coursera, Udacity)',
                '技术博客和论文'
            ],
            '数据集': [
                'Kaggle公开数据集',
                'UCI机器学习数据库',
                '行业公开数据'
            ],
            '开源项目': []
        }

        if tech:
            for t in tech[:3]:
                resources['开源项目'].append({
                    'name': t['title'],
                    'url': t['url'],
                    'description': t['description']
                })

        return resources

    def _generate_challenges(self, keyword, difficulty):
        """生成常见挑战"""
        challenges = [
            {
                'challenge': '数据质量问题',
                'description': '训练数据不足或质量不高',
                'solution': '数据增强、迁移学习、主动学习'
            },
            {
                'challenge': '模型性能不佳',
                'description': '模型准确率达不到要求',
                'solution': '调整模型架构、超参数优化、集成学习'
            },
            {
                'challenge': '过拟合',
                'description': '模型在训练集上表现好但泛化能力差',
                'solution': '正则化、Dropout、数据增强、早停'
            }
        ]

        if difficulty in ['intermediate', 'advanced']:
            challenges.extend([
                {
                    'challenge': '计算资源限制',
                    'description': '训练时间过长或硬件资源不足',
                    'solution': '模型压缩、分布式训练、云计算平台'
                },
                {
                    'challenge': '部署和维护',
                    'description': '模型上线后的性能监控和更新',
                    'solution': 'MLOps流程、持续集成、A/B测试'
                }
            ])

        return challenges

    def _generate_discussion_background(self, keyword, trends, industry):
        """生成讨论背景"""
        background = f"近年来，{keyword}技术发展迅速，应用日益广泛。"

        if trends:
            trend = trends[0]
            background += f"\n\n{trend['summary']}"

        if industry:
            app = industry[0]
            background += f"\n\n在{app['industry']}领域，{app['company']}的实践表明：{app['description']}"

        background += f"\n\n这些发展在带来巨大价值的同时，也引发了关于技术伦理、社会影响等方面的深入思考。"

        return background

    def _generate_core_issues(self, keyword, focus):
        """生成核心议题"""
        issues = []

        if focus == 'ethics':
            issues = [
                f"{keyword}系统的算法偏见和公平性问题",
                f"{keyword}应用中的隐私保护挑战",
                f"{keyword}决策的透明性和可解释性",
                "技术开发者和使用者的责任边界"
            ]
        elif focus == 'social':
            issues = [
                f"{keyword}对就业市场的影响",
                f"{keyword}带来的数字鸿沟问题",
                "教育体系如何适应技术变革",
                "社会如何管理技术风险"
            ]
        elif focus == 'business':
            issues = [
                f"{keyword}的商业模式创新",
                f"{keyword}投资的风险与回报",
                "技术竞争与合作的策略选择",
                "可持续发展的商业实践"
            ]
        else:  # theory
            issues = [
                f"{keyword}的技术瓶颈和突破方向",
                f"{keyword}与其他技术的融合",
                "基础研究与应用研究的平衡",
                "开源vs闭源的发展路径"
            ]

        return issues

    def _generate_analysis_guide(self, keyword):
        """生成分析指南"""
        guide = {
            '步骤1：理解背景': '全面了解案例背景和相关技术',
            '步骤2：识别问题': '明确核心问题和相关方利益',
            '步骤3：多角度分析': '从技术、商业、伦理等多个维度分析',
            '步骤4：提出方案': '提出可行的解决方案或改进建议',
            '步骤5：评估影响': '评估方案的效果和潜在影响',
            '步骤6：总结反思': '总结经验教训和启示'
        }

        return guide

    def _generate_discussion_readings(self, trends, industry):
        """生成讨论阅读材料"""
        readings = []

        if trends:
            for trend in trends[:2]:
                readings.append({
                    'title': trend['title'],
                    'type': trend['type'],
                    'summary': trend['summary'],
                    'source': trend.get('source', '未知来源')
                })

        if industry:
            app = industry[0]
            readings.append({
                'title': app['title'],
                'type': '应用案例',
                'summary': app['description'],
                'source': app.get('source', '行业报告')
            })

        return readings

    def _get_difficulty_label(self, difficulty):
        """获取难度标签"""
        labels = {
            'beginner': '初级',
            'intermediate': '中级',
            'advanced': '高级'
        }
        return labels.get(difficulty, '中级')

    def _get_audience_label(self, audience):
        """获取受众标签"""
        labels = {
            'undergraduate': '本科生',
            'graduate': '研究生',
            'professional': '从业人员'
        }
        return labels.get(audience, '本科生')

    def _estimate_reading_time(self, case):
        """估算阅读时间（分钟）"""
        # 简单估算：假设每分钟阅读200字
        content_str = json.dumps(case, ensure_ascii=False)
        word_count = len(content_str)
        reading_time = max(5, word_count // 200)
        return reading_time

    def export(self, case, format_type='markdown'):
        """
        导出案例
        :param case: 案例数据
        :param format_type: 导出格式
        :return: 导出的内容
        """
        if format_type == 'markdown':
            return self._export_markdown(case)
        elif format_type == 'html':
            return self._export_html(case)
        else:
            return json.dumps(case, ensure_ascii=False, indent=2)

    def _export_markdown(self, case):
        """导出为Markdown格式"""
        md = f"# {case.get('title', '教学案例')}\n\n"

        md += f"**案例类型**: {case.get('case_type', 'N/A')}\n\n"
        md += f"**难度等级**: {case.get('difficulty_level', 'N/A')}\n\n"
        md += f"**目标受众**: {case.get('target_audience', 'N/A')}\n\n"

        if 'background' in case:
            md += f"## 背景介绍\n\n{case['background']}\n\n"

        if 'problem_statement' in case:
            md += f"## 问题陈述\n\n{case['problem_statement']}\n\n"

        if 'learning_objectives' in case:
            md += "## 学习目标\n\n"
            for obj in case['learning_objectives']:
                md += f"- {obj}\n"
            md += "\n"

        if 'technical_foundation' in case:
            md += f"## 技术基础\n\n{case['technical_foundation']}\n\n"

        if 'discussion_questions' in case:
            md += "## 讨论问题\n\n"
            for i, q in enumerate(case['discussion_questions'], 1):
                md += f"{i}. {q}\n"
            md += "\n"

        md += f"---\n\n*生成时间: {case.get('metadata', {}).get('generated_at', 'N/A')}*\n"

        return md

    def _export_html(self, case):
        """导出为HTML格式"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{case.get('title', '教学案例')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
        .metadata {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{case.get('title', '教学案例')}</h1>

    <div class="metadata">
        <p><strong>案例类型</strong>: {case.get('case_type', 'N/A')}</p>
        <p><strong>难度等级</strong>: {case.get('difficulty_level', 'N/A')}</p>
        <p><strong>目标受众</strong>: {case.get('target_audience', 'N/A')}</p>
    </div>
"""

        if 'background' in case:
            html += f"<h2>背景介绍</h2><p>{case['background']}</p>"

        if 'problem_statement' in case:
            html += f"<h2>问题陈述</h2><p>{case['problem_statement']}</p>"

        html += """
</body>
</html>
"""

        return html


if __name__ == '__main__':
    # 测试代码
    generator = CaseGenerator()

    # 模拟搜索结果
    source_data = {
        'papers': [
            {
                'title': 'Deep Learning for Computer Vision',
                'authors': ['Author 1', 'Author 2'],
                'summary': 'This paper presents...',
                'published': '2024-01-15',
                'link': 'https://arxiv.org/abs/xxxx'
            }
        ],
        'tech': [],
        'products': [],
        'industry': [],
        'trends': []
    }

    # 生成案例
    case = generator.generate(
        keyword='计算机视觉',
        source_data=source_data,
        case_type='problem',
        difficulty='intermediate',
        focus='theory',
        audience='undergraduate'
    )

    print("案例标题:", case['title'])
    print("\n学习目标:")
    for obj in case['learning_objectives']:
        print(f"  - {obj}")
