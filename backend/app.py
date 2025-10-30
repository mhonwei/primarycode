"""
AI案例智库系统 - 后端主应用
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawlers.paper_crawler import PaperCrawler
from crawlers.tech_crawler import TechCrawler
from crawlers.product_crawler import ProductCrawler
from crawlers.industry_crawler import IndustryCrawler
from crawlers.trend_crawler import TrendCrawler
from generators.case_generator import CaseGenerator

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 初始化爬虫
paper_crawler = PaperCrawler()
tech_crawler = TechCrawler()
product_crawler = ProductCrawler()
industry_crawler = IndustryCrawler()
trend_crawler = TrendCrawler()

# 初始化案例生成器
case_generator = CaseGenerator()


@app.route('/')
def index():
    """主页"""
    return jsonify({
        'name': 'AI案例智库系统',
        'version': '1.0.0',
        'status': 'running'
    })


@app.route('/api/search', methods=['POST'])
def search():
    """
    统一搜索接口
    请求体: {
        "keyword": "搜索关键词",
        "search_type": "paper|tech|product|industry|trend|all",
        "limit": 10
    }
    """
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        search_type = data.get('search_type', 'all')
        limit = data.get('limit', 10)

        if not keyword:
            return jsonify({'error': '请提供搜索关键词'}), 400

        results = {}

        # 根据搜索类型调用相应的爬虫
        if search_type == 'all' or search_type == 'paper':
            results['papers'] = paper_crawler.search(keyword, limit)

        if search_type == 'all' or search_type == 'tech':
            results['tech'] = tech_crawler.search(keyword, limit)

        if search_type == 'all' or search_type == 'product':
            results['products'] = product_crawler.search(keyword, limit)

        if search_type == 'all' or search_type == 'industry':
            results['industry'] = industry_crawler.search(keyword, limit)

        if search_type == 'all' or search_type == 'trend':
            results['trends'] = trend_crawler.search(keyword, limit)

        return jsonify({
            'success': True,
            'keyword': keyword,
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-case', methods=['POST'])
def generate_case():
    """
    生成教学案例
    请求体: {
        "keyword": "关键词",
        "source_data": {...},  # 搜索结果数据
        "case_type": "problem|project|discussion",  # 案例类型
        "difficulty": "beginner|intermediate|advanced",  # 难度
        "focus": "theory|business|social|ethics",  # 侧重点
        "audience": "undergraduate|graduate|professional",  # 受众
        "word_limit": 1000
    }
    """
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        source_data = data.get('source_data', {})
        case_type = data.get('case_type', 'problem')
        difficulty = data.get('difficulty', 'intermediate')
        focus = data.get('focus', 'theory')
        audience = data.get('audience', 'undergraduate')
        word_limit = data.get('word_limit', 1000)

        if not keyword:
            return jsonify({'error': '请提供关键词'}), 400

        # 生成案例
        case = case_generator.generate(
            keyword=keyword,
            source_data=source_data,
            case_type=case_type,
            difficulty=difficulty,
            focus=focus,
            audience=audience,
            word_limit=word_limit
        )

        return jsonify({
            'success': True,
            'case': case
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export-case', methods=['POST'])
def export_case():
    """
    导出案例
    请求体: {
        "case": {...},  # 案例数据
        "format": "markdown|html|pdf"  # 导出格式
    }
    """
    try:
        data = request.get_json()
        case = data.get('case', {})
        format_type = data.get('format', 'markdown')

        if not case:
            return jsonify({'error': '请提供案例数据'}), 400

        # 导出案例
        exported_content = case_generator.export(case, format_type)

        return jsonify({
            'success': True,
            'content': exported_content,
            'format': format_type
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'crawlers': {
            'paper': 'active',
            'tech': 'active',
            'product': 'active',
            'industry': 'active',
            'trend': 'active'
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("AI案例智库系统 - 后端服务")
    print("=" * 60)
    print("服务地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api/health")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
