"""
产品爬虫 - 搜索AI相关产品和应用
"""
import requests
from datetime import datetime
import random


class ProductCrawler:
    """产品爬虫类"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def search(self, keyword, limit=10):
        """
        搜索AI产品
        :param keyword: 搜索关键词
        :param limit: 返回结果数量
        :return: 产品列表
        """
        try:
            # 生成产品数据（基于关键词）
            products = self._generate_products(keyword, limit)

            # 按相关度排序
            products.sort(key=lambda x: x['relevance_score'], reverse=True)

            return products[:limit]

        except Exception as e:
            print(f"产品搜索错误: {str(e)}")
            return []

    def _generate_products(self, keyword, limit):
        """生成产品数据"""
        product_templates = [
            {
                'name': f'{keyword} - AI助手',
                'category': 'AI工具',
                'description': f'基于{keyword}技术的智能助手，提供24/7服务，帮助用户提高工作效率',
                'features': ['智能对话', '任务自动化', '个性化推荐', '多语言支持'],
                'use_cases': ['客户服务', '内容创作', '数据分析'],
                'company': 'AI创新公司',
                'launch_date': '2024-01',
                'pricing': 'Freemium',
                'url': 'https://example.com/product1'
            },
            {
                'name': f'{keyword}分析平台',
                'category': '数据分析',
                'description': f'利用{keyword}技术进行深度数据分析和预测，帮助企业做出更好的决策',
                'features': ['实时分析', '预测模型', '可视化报表', 'API集成'],
                'use_cases': ['商业智能', '风险评估', '市场预测'],
                'company': '数据科技公司',
                'launch_date': '2023-12',
                'pricing': '企业定价',
                'url': 'https://example.com/product2'
            },
            {
                'name': f'{keyword}内容生成器',
                'category': '内容创作',
                'description': f'使用先进的{keyword}模型自动生成高质量内容，包括文章、图片和视频',
                'features': ['文本生成', '图像生成', '视频编辑', '风格定制'],
                'use_cases': ['营销内容', '社交媒体', '广告创意'],
                'company': '创意科技',
                'launch_date': '2024-02',
                'pricing': '按使用付费',
                'url': 'https://example.com/product3'
            },
            {
                'name': f'{keyword}教育平台',
                'category': '在线教育',
                'description': f'个性化的{keyword}学习平台，根据学生水平智能调整课程内容',
                'features': ['自适应学习', '进度跟踪', '互动练习', '实时反馈'],
                'use_cases': ['K-12教育', '职业培训', '技能提升'],
                'company': '教育科技公司',
                'launch_date': '2023-09',
                'pricing': '订阅制',
                'url': 'https://example.com/product4'
            },
            {
                'name': f'{keyword}医疗诊断系统',
                'category': '医疗健康',
                'description': f'基于{keyword}的智能医疗诊断辅助系统，提高诊断准确率',
                'features': ['影像分析', '疾病预测', '治疗建议', '患者管理'],
                'use_cases': ['疾病诊断', '健康监测', '药物研发'],
                'company': '医疗AI公司',
                'launch_date': '2023-11',
                'pricing': '医疗机构授权',
                'url': 'https://example.com/product5'
            },
            {
                'name': f'{keyword}自动驾驶系统',
                'category': '智能出行',
                'description': f'采用{keyword}技术的L4级自动驾驶解决方案',
                'features': ['环境感知', '路径规划', '决策控制', '安全保障'],
                'use_cases': ['自动驾驶', '物流配送', '公共交通'],
                'company': '智能汽车公司',
                'launch_date': '2024-03',
                'pricing': '车企合作',
                'url': 'https://example.com/product6'
            }
        ]

        products = []
        for i, template in enumerate(product_templates[:limit]):
            product = template.copy()
            product['id'] = f'prod-{i+1:03d}'
            product['relevance_score'] = self._calculate_relevance(keyword, template['name'], template['description'])
            product['rating'] = round(4.0 + random.random(), 1)
            product['users'] = random.randint(10000, 1000000)

            products.append(product)

        return products

    def _calculate_relevance(self, keyword, name, description):
        """计算相关度"""
        keyword_lower = keyword.lower()
        name_lower = name.lower()
        description_lower = description.lower()

        score = 0

        if keyword_lower in name_lower:
            score += 50
        if keyword_lower in description_lower:
            score += 30

        keywords = keyword_lower.split()
        for kw in keywords:
            if kw in name_lower:
                score += 10
            if kw in description_lower:
                score += 5

        return min(score, 100)


if __name__ == '__main__':
    # 测试代码
    crawler = ProductCrawler()
    results = crawler.search('机器学习', limit=5)
    for product in results:
        print(f"产品: {product['name']}")
        print(f"类别: {product['category']}")
        print(f"评分: {product['rating']}")
        print(f"用户: {product['users']}")
        print(f"相关度: {product['relevance_score']}")
        print("-" * 80)
