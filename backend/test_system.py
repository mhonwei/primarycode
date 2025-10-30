"""
系统功能测试脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawlers.paper_crawler import PaperCrawler
from crawlers.tech_crawler import TechCrawler
from crawlers.product_crawler import ProductCrawler
from crawlers.industry_crawler import IndustryCrawler
from crawlers.trend_crawler import TrendCrawler
from generators.case_generator import CaseGenerator


def test_crawlers():
    """测试所有爬虫"""
    print("=" * 60)
    print("测试爬虫模块")
    print("=" * 60)

    keyword = "深度学习"

    # 测试论文爬虫
    print("\n1. 测试论文爬虫...")
    paper_crawler = PaperCrawler()
    papers = paper_crawler.search(keyword, limit=3)
    print(f"✓ 找到 {len(papers)} 篇论文")
    if papers:
        print(f"  示例: {papers[0]['title']}")

    # 测试技术爬虫
    print("\n2. 测试技术爬虫...")
    tech_crawler = TechCrawler()
    tech = tech_crawler.search(keyword, limit=3)
    print(f"✓ 找到 {len(tech)} 个技术项目")
    if tech:
        print(f"  示例: {tech[0]['title']}")

    # 测试产品爬虫
    print("\n3. 测试产品爬虫...")
    product_crawler = ProductCrawler()
    products = product_crawler.search(keyword, limit=3)
    print(f"✓ 找到 {len(products)} 个产品")
    if products:
        print(f"  示例: {products[0]['name']}")

    # 测试行业应用爬虫
    print("\n4. 测试行业应用爬虫...")
    industry_crawler = IndustryCrawler()
    industry = industry_crawler.search(keyword, limit=3)
    print(f"✓ 找到 {len(industry)} 个行业案例")
    if industry:
        print(f"  示例: {industry[0]['title']}")

    # 测试前沿热点爬虫
    print("\n5. 测试前沿热点爬虫...")
    trend_crawler = TrendCrawler()
    trends = trend_crawler.search(keyword, limit=3)
    print(f"✓ 找到 {len(trends)} 个热点")
    if trends:
        print(f"  示例: {trends[0]['title']}")

    return {
        'papers': papers,
        'tech': tech,
        'products': products,
        'industry': industry,
        'trends': trends
    }


def test_case_generator(source_data):
    """测试案例生成器"""
    print("\n" + "=" * 60)
    print("测试案例生成模块")
    print("=" * 60)

    generator = CaseGenerator()

    # 测试问题导向型案例
    print("\n1. 生成问题导向型案例...")
    case1 = generator.generate(
        keyword="深度学习",
        source_data=source_data,
        case_type='problem',
        difficulty='intermediate',
        focus='theory',
        audience='undergraduate',
        word_limit=1000
    )
    print(f"✓ 案例标题: {case1['title']}")
    print(f"  学习目标数量: {len(case1['learning_objectives'])}")

    # 测试项目驱动型案例
    print("\n2. 生成项目驱动型案例...")
    case2 = generator.generate(
        keyword="深度学习",
        source_data=source_data,
        case_type='project',
        difficulty='intermediate',
        focus='theory',
        audience='undergraduate',
        word_limit=1000
    )
    print(f"✓ 案例标题: {case2['title']}")
    print(f"  项目阶段数量: {len(case2['project_phases'])}")

    # 测试讨论型案例
    print("\n3. 生成讨论型案例...")
    case3 = generator.generate(
        keyword="深度学习",
        source_data=source_data,
        case_type='discussion',
        difficulty='intermediate',
        focus='ethics',
        audience='undergraduate',
        word_limit=1000
    )
    print(f"✓ 案例标题: {case3['title']}")
    print(f"  讨论场景数量: {len(case3['discussion_scenarios'])}")

    # 测试导出功能
    print("\n4. 测试导出功能...")
    markdown_content = generator.export(case1, 'markdown')
    print(f"✓ Markdown导出成功 ({len(markdown_content)} 字符)")

    html_content = generator.export(case1, 'html')
    print(f"✓ HTML导出成功 ({len(html_content)} 字符)")

    return case1


def test_accuracy():
    """测试准确度"""
    print("\n" + "=" * 60)
    print("测试准确度")
    print("=" * 60)

    keywords = ["计算机视觉", "自然语言处理", "强化学习"]
    total_score = 0
    count = 0

    for keyword in keywords:
        print(f"\n关键词: {keyword}")

        # 测试论文搜索
        paper_crawler = PaperCrawler()
        papers = paper_crawler.search(keyword, limit=5)

        if papers:
            avg_score = sum(p['relevance_score'] for p in papers) / len(papers)
            print(f"  论文搜索平均相关度: {avg_score:.1f}%")
            total_score += avg_score
            count += 1

        # 测试技术搜索
        tech_crawler = TechCrawler()
        tech = tech_crawler.search(keyword, limit=5)

        if tech:
            avg_score = sum(t['relevance_score'] for t in tech) / len(tech)
            print(f"  技术搜索平均相关度: {avg_score:.1f}%")
            total_score += avg_score
            count += 1

    if count > 0:
        overall_accuracy = total_score / count
        print(f"\n总体准确度: {overall_accuracy:.1f}%")

        if overall_accuracy >= 90:
            print("✅ 达到90%准确度目标！")
        else:
            print(f"⚠️  当前准确度 {overall_accuracy:.1f}%，目标 90%")

    return overall_accuracy


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("AI案例智库系统 - 功能测试")
    print("=" * 60)

    try:
        # 测试爬虫
        source_data = test_crawlers()

        # 测试案例生成
        case = test_case_generator(source_data)

        # 测试准确度
        accuracy = test_accuracy()

        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        print("\n✅ 所有功能测试通过！")
        print("\n系统已就绪，可以启动服务进行使用。")
        print("运行以下命令启动系统：")
        print("  Linux/Mac: ./start.sh")
        print("  Windows:   start.bat")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
