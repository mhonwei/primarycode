"""
数据管理模块 - 健康内容网络爬虫系统
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict
import pandas as pd
import logging
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataManager:
    """数据管理类"""

    def __init__(self):
        self.output_dir = config.EXPORT_CONFIG['output_dir']
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"创建输出目录: {self.output_dir}")

    def save_to_json(self, data: List[Dict], filename: str = None) -> str:
        """
        保存数据为JSON格式

        Args:
            data: 要保存的数据列表
            filename: 文件名（可选）

        Returns:
            保存的文件路径
        """
        if filename is None:
            filename = f"health_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到 JSON 文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存 JSON 文件失败: {e}")
            raise

    def save_to_csv(self, data: List[Dict], filename: str = None) -> str:
        """
        保存数据为CSV格式

        Args:
            data: 要保存的数据列表
            filename: 文件名（可选）

        Returns:
            保存的文件路径
        """
        if not data:
            logger.warning("没有数据可保存")
            return ""

        if filename is None:
            filename = f"health_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = os.path.join(self.output_dir, filename)

        try:
            # 获取所有可能的字段
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            fieldnames = sorted(list(fieldnames))

            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"数据已保存到 CSV 文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存 CSV 文件失败: {e}")
            raise

    def save_to_excel(self, data: List[Dict], filename: str = None) -> str:
        """
        保存数据为Excel格式

        Args:
            data: 要保存的数据列表
            filename: 文件名（可选）

        Returns:
            保存的文件路径
        """
        if not data:
            logger.warning("没有数据可保存")
            return ""

        if filename is None:
            filename = f"health_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        filepath = os.path.join(self.output_dir, filename)

        try:
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"数据已保存到 Excel 文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存 Excel 文件失败: {e}")
            raise

    def save_to_txt(self, data: List[Dict], filename: str = None) -> str:
        """
        保存数据为TXT格式（可读性强）

        Args:
            data: 要保存的数据列表
            filename: 文件名（可选）

        Returns:
            保存的文件路径
        """
        if not data:
            logger.warning("没有数据可保存")
            return ""

        if filename is None:
            filename = f"health_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for i, article in enumerate(data, 1):
                    f.write(f"{'=' * 80}\n")
                    f.write(f"文章 {i}\n")
                    f.write(f"{'=' * 80}\n\n")

                    f.write(f"标题: {article.get('title', '无标题')}\n")
                    f.write(f"分类: {article.get('category', '未分类')}\n")
                    f.write(f"作者: {article.get('author', '未知')}\n")
                    f.write(f"日期: {article.get('date', '未知')}\n")
                    f.write(f"URL: {article.get('url', '无')}\n")

                    if article.get('keywords'):
                        f.write(f"关键词: {', '.join(article['keywords'])}\n")

                    f.write(f"字数: {article.get('word_count', 0)}\n")
                    f.write(f"抓取时间: {article.get('scraped_time', '未知')}\n")
                    f.write(f"\n内容:\n{'-' * 80}\n")
                    f.write(f"{article.get('content', '无内容')}\n\n")

            logger.info(f"数据已保存到 TXT 文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存 TXT 文件失败: {e}")
            raise

    def save_to_all_formats(self, data: List[Dict], base_filename: str = None) -> Dict[str, str]:
        """
        保存数据到所有格式

        Args:
            data: 要保存的数据列表
            base_filename: 基础文件名（可选）

        Returns:
            包含所有格式文件路径的字典
        """
        if not data:
            logger.warning("没有数据可保存")
            return {}

        if base_filename is None:
            base_filename = f"health_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        results = {}

        try:
            results['json'] = self.save_to_json(data, f"{base_filename}.json")
            results['csv'] = self.save_to_csv(data, f"{base_filename}.csv")
            results['excel'] = self.save_to_excel(data, f"{base_filename}.xlsx")
            results['txt'] = self.save_to_txt(data, f"{base_filename}.txt")
            logger.info(f"数据已保存到所有格式")
        except Exception as e:
            logger.error(f"保存数据时出错: {e}")

        return results

    def load_from_json(self, filepath: str) -> List[Dict]:
        """
        从JSON文件加载数据

        Args:
            filepath: JSON文件路径

        Returns:
            数据列表
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"从 JSON 文件加载了 {len(data)} 条数据")
            return data
        except Exception as e:
            logger.error(f"加载 JSON 文件失败: {e}")
            return []

    def get_statistics(self, data: List[Dict]) -> Dict:
        """
        获取数据统计信息

        Args:
            data: 数据列表

        Returns:
            统计信息字典
        """
        if not data:
            return {
                'total_articles': 0,
                'categories': {},
                'total_words': 0,
                'average_words': 0
            }

        stats = {
            'total_articles': len(data),
            'categories': {},
            'total_words': 0,
            'sources': set()
        }

        for article in data:
            # 统计分类
            category = article.get('category', '未分类')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1

            # 统计字数
            word_count = article.get('word_count', 0)
            stats['total_words'] += word_count

            # 统计来源
            if article.get('url'):
                from urllib.parse import urlparse
                domain = urlparse(article['url']).netloc
                stats['sources'].add(domain)

        stats['average_words'] = stats['total_words'] // stats['total_articles'] if stats['total_articles'] > 0 else 0
        stats['unique_sources'] = len(stats['sources'])
        stats['sources'] = list(stats['sources'])

        return stats


class URLManager:
    """URL管理类"""

    def __init__(self):
        self.urls_file = os.path.join(config.EXPORT_CONFIG['output_dir'], 'urls.json')
        self.urls = self.load_urls()

    def load_urls(self) -> Dict[str, List[str]]:
        """加载保存的URL列表"""
        if os.path.exists(self.urls_file):
            try:
                with open(self.urls_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载 URL 文件失败: {e}")
        return {}

    def save_urls(self):
        """保存URL列表"""
        try:
            os.makedirs(os.path.dirname(self.urls_file), exist_ok=True)
            with open(self.urls_file, 'w', encoding='utf-8') as f:
                json.dump(self.urls, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存 URL 文件失败: {e}")

    def add_url(self, category: str, url: str):
        """添加URL到指定分类"""
        if category not in self.urls:
            self.urls[category] = []
        if url not in self.urls[category]:
            self.urls[category].append(url)
            self.save_urls()

    def add_urls(self, category: str, urls: List[str]):
        """批量添加URL"""
        if category not in self.urls:
            self.urls[category] = []
        for url in urls:
            if url not in self.urls[category]:
                self.urls[category].append(url)
        self.save_urls()

    def get_urls(self, category: str) -> List[str]:
        """获取指定分类的URL列表"""
        return self.urls.get(category, [])

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self.urls.keys())

    def remove_url(self, category: str, url: str):
        """删除指定URL"""
        if category in self.urls and url in self.urls[category]:
            self.urls[category].remove(url)
            self.save_urls()
