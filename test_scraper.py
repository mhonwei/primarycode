"""
测试脚本 - 验证爬虫系统的基本功能
"""

import sys
import logging
from scraper import HealthContentScraper
from data_manager import DataManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_scraper_initialization():
    """测试爬虫初始化"""
    try:
        scraper = HealthContentScraper()
        logger.info("✓ 爬虫初始化成功")
        return True
    except Exception as e:
        logger.error(f"✗ 爬虫初始化失败: {e}")
        return False


def test_data_manager():
    """测试数据管理器"""
    try:
        data_manager = DataManager()
        logger.info("✓ 数据管理器初始化成功")

        # 测试数据
        test_data = [
            {
                'title': '测试文章1',
                'url': 'https://example.com/test1',
                'content': '这是一篇测试文章的内容。包含了健康相关的信息。',
                'category': '健康管理',
                'author': '测试作者',
                'date': '2025-10-30',
                'keywords': ['健康', '测试'],
                'scraped_time': '2025-10-30 12:00:00',
                'word_count': 20
            },
            {
                'title': '测试文章2',
                'url': 'https://example.com/test2',
                'content': '这是第二篇测试文章。关于饮食营养的内容。',
                'category': '饮食管理',
                'author': '测试作者2',
                'date': '2025-10-30',
                'keywords': ['饮食', '营养'],
                'scraped_time': '2025-10-30 12:00:00',
                'word_count': 18
            }
        ]

        # 测试导出功能
        try:
            data_manager.save_to_json(test_data, 'test_data.json')
            logger.info("✓ JSON 导出测试成功")
        except Exception as e:
            logger.error(f"✗ JSON 导出测试失败: {e}")
            return False

        try:
            data_manager.save_to_csv(test_data, 'test_data.csv')
            logger.info("✓ CSV 导出测试成功")
        except Exception as e:
            logger.error(f"✗ CSV 导出测试失败: {e}")
            return False

        try:
            data_manager.save_to_txt(test_data, 'test_data.txt')
            logger.info("✓ TXT 导出测试成功")
        except Exception as e:
            logger.error(f"✗ TXT 导出测试失败: {e}")
            return False

        # 测试统计功能
        stats = data_manager.get_statistics(test_data)
        if stats['total_articles'] == 2:
            logger.info("✓ 统计功能测试成功")
        else:
            logger.error(f"✗ 统计功能测试失败: 期望2篇文章，实际{stats['total_articles']}篇")
            return False

        return True

    except Exception as e:
        logger.error(f"✗ 数据管理器测试失败: {e}")
        return False


def test_html_parsing():
    """测试 HTML 解析功能"""
    try:
        scraper = HealthContentScraper()

        # 简单的 HTML 测试
        test_html = """
        <html>
        <head>
            <title>测试文章标题</title>
            <meta name="author" content="测试作者">
            <meta name="keywords" content="健康,营养,测试">
        </head>
        <body>
            <article>
                <h1>测试文章标题</h1>
                <p>这是第一段测试内容。</p>
                <p>这是第二段测试内容，包含更多的健康信息。</p>
            </article>
        </body>
        </html>
        """

        article = scraper.parse_article(test_html, "https://test.com/article")

        if article['title'] and article['content']:
            logger.info(f"✓ HTML 解析测试成功")
            logger.info(f"  - 标题: {article['title']}")
            logger.info(f"  - 内容长度: {len(article['content'])} 字符")
            return True
        else:
            logger.error("✗ HTML 解析测试失败: 无法提取标题或内容")
            return False

    except Exception as e:
        logger.error(f"✗ HTML 解析测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("开始运行健康内容爬虫系统测试")
    logger.info("=" * 60)
    logger.info("")

    results = []

    # 运行测试
    logger.info("1. 测试爬虫初始化...")
    results.append(test_scraper_initialization())
    logger.info("")

    logger.info("2. 测试 HTML 解析功能...")
    results.append(test_html_parsing())
    logger.info("")

    logger.info("3. 测试数据管理器...")
    results.append(test_data_manager())
    logger.info("")

    # 总结
    logger.info("=" * 60)
    passed = sum(results)
    total = len(results)
    logger.info(f"测试完成: {passed}/{total} 通过")
    logger.info("=" * 60)

    if passed == total:
        logger.info("✓ 所有测试通过！系统可以正常使用。")
        return 0
    else:
        logger.warning(f"✗ 有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
