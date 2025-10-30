"""
网页爬虫模块 - 健康内容网络爬虫系统
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Optional
import config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthContentScraper:
    """健康内容爬虫类"""

    def __init__(self):
        self.headers = config.HEADERS
        self.timeout = config.SCRAPER_CONFIG['timeout']
        self.max_retries = config.SCRAPER_CONFIG['max_retries']
        self.delay = config.SCRAPER_CONFIG['delay_between_requests']
        self.scraped_data = []

    def fetch_page(self, url: str) -> Optional[str]:
        """
        获取网页内容

        Args:
            url: 目标URL

        Returns:
            网页HTML内容，失败返回None
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response.text
            except requests.RequestException as e:
                logger.warning(f"尝试 {attempt + 1}/{self.max_retries} 失败: {url}, 错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay)
                else:
                    logger.error(f"无法获取页面: {url}")
                    return None
        return None

    def parse_article(self, html: str, url: str) -> Dict:
        """
        解析文章内容

        Args:
            html: HTML内容
            url: 文章URL

        Returns:
            包含文章信息的字典
        """
        soup = BeautifulSoup(html, 'lxml')

        # 提取标题
        title = self._extract_title(soup)

        # 提取内容
        content = self._extract_content(soup)

        # 提取作者
        author = self._extract_author(soup)

        # 提取日期
        date = self._extract_date(soup)

        # 提取关键词
        keywords = self._extract_keywords(soup)

        article = {
            'title': title,
            'url': url,
            'content': content,
            'author': author,
            'date': date,
            'keywords': keywords,
            'scraped_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'word_count': len(content) if content else 0
        }

        return article

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 尝试多种标题选择器
        title_selectors = [
            ('h1', {}),
            ('title', {}),
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'title'})
        ]

        for tag, attrs in title_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', '未知标题')
                return element.get_text(strip=True)

        return '未知标题'

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        # 移除脚本和样式标签
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # 尝试多种内容选择器
        content_selectors = [
            {'name': 'article'},
            {'class_': re.compile(r'(content|article|post|entry)', re.I)},
            {'id': re.compile(r'(content|article|post|entry)', re.I)},
            {'name': 'main'},
        ]

        for selector in content_selectors:
            element = soup.find(**selector)
            if element:
                paragraphs = element.find_all(['p', 'h2', 'h3', 'h4', 'li'])
                content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                if len(content) > 100:  # 确保内容足够长
                    return content

        # 如果没有找到，尝试获取所有段落
        paragraphs = soup.find_all('p')
        content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        return content if content else '无法提取内容'

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者"""
        author_selectors = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('span', {'class_': re.compile(r'author', re.I)}),
            ('a', {'rel': 'author'})
        ]

        for tag, attrs in author_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', '未知作者')
                return element.get_text(strip=True)

        return '未知作者'

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取发布日期"""
        date_selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publish_date'}),
            ('time', {}),
            ('span', {'class_': re.compile(r'(date|time|published)', re.I)})
        ]

        for tag, attrs in date_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', '未知日期')
                if tag == 'time' and element.get('datetime'):
                    return element.get('datetime')
                return element.get_text(strip=True)

        return '未知日期'

    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """提取关键词"""
        keywords = []

        # 从 meta 标签提取
        meta_keywords = soup.find('meta', {'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [k.strip() for k in meta_keywords.get('content').split(',')]

        return keywords

    def search_by_category(self, category: str, max_results: int = 10) -> List[Dict]:
        """
        根据分类搜索内容

        Args:
            category: 内容分类
            max_results: 最大结果数

        Returns:
            文章列表
        """
        articles = []

        if category not in config.CONTENT_CATEGORIES:
            logger.error(f"未知分类: {category}")
            return articles

        category_config = config.CONTENT_CATEGORIES[category]
        keywords = category_config['keywords']

        logger.info(f"开始搜索分类: {category}, 关键词: {keywords}")

        # 这里可以实现具体的搜索逻辑
        # 由于不同网站的搜索接口不同，这里提供一个通用框架

        return articles

    def scrape_url(self, url: str, category: str = "未分类") -> Optional[Dict]:
        """
        抓取单个URL

        Args:
            url: 目标URL
            category: 内容分类

        Returns:
            文章信息字典
        """
        logger.info(f"正在抓取: {url}")

        html = self.fetch_page(url)
        if not html:
            return None

        article = self.parse_article(html, url)
        article['category'] = category

        time.sleep(self.delay)  # 礼貌性延迟

        return article

    def scrape_urls(self, urls: List[str], category: str = "未分类",
                    progress_callback=None) -> List[Dict]:
        """
        批量抓取URL列表

        Args:
            urls: URL列表
            category: 内容分类
            progress_callback: 进度回调函数

        Returns:
            文章列表
        """
        articles = []
        total = len(urls)

        for i, url in enumerate(urls):
            try:
                article = self.scrape_url(url, category)
                if article:
                    articles.append(article)
                    logger.info(f"成功抓取: {article['title']}")

                # 更新进度
                if progress_callback:
                    progress = (i + 1) / total * 100
                    progress_callback(progress, f"已完成 {i + 1}/{total}")

            except Exception as e:
                logger.error(f"抓取失败 {url}: {e}")
                continue

        return articles

    def search_pubmed(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        搜索 PubMed 学术文章

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            文章列表
        """
        articles = []

        # PubMed API 搜索
        search_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={query}&format=abstract"

        try:
            html = self.fetch_page(search_url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                # 解析搜索结果
                # 这里需要根据 PubMed 的实际页面结构进行调整
                result_items = soup.find_all('article', class_='full-docsum', limit=max_results)

                for item in result_items:
                    try:
                        title_elem = item.find('a', class_='docsum-title')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = urljoin("https://pubmed.ncbi.nlm.nih.gov", title_elem.get('href', ''))

                            articles.append({
                                'title': title,
                                'url': link,
                                'source': 'PubMed',
                                'category': '学术论文'
                            })
                    except Exception as e:
                        logger.error(f"解析 PubMed 结果时出错: {e}")
                        continue
        except Exception as e:
            logger.error(f"搜索 PubMed 时出错: {e}")

        return articles


class CustomSourceScraper:
    """自定义数据源爬虫"""

    def __init__(self):
        self.scraper = HealthContentScraper()

    def scrape_custom_urls(self, urls: List[str], category: str,
                          progress_callback=None) -> List[Dict]:
        """
        抓取用户自定义的URL列表

        Args:
            urls: URL列表
            category: 内容分类
            progress_callback: 进度回调函数

        Returns:
            文章列表
        """
        return self.scraper.scrape_urls(urls, category, progress_callback)
