"""
配置文件 - 健康内容网络爬虫系统
"""

# 内容分类
CONTENT_CATEGORIES = {
    "健康管理": {
        "keywords": ["健康管理", "health management", "wellness", "保健"],
        "sources": [
            "https://www.healthline.com",
            "https://www.mayoclinic.org",
            "https://www.webmd.com"
        ]
    },
    "饮食管理": {
        "keywords": ["饮食", "营养", "nutrition", "diet", "食物"],
        "sources": [
            "https://www.nutrition.gov",
            "https://www.eatright.org"
        ]
    },
    "疾病预防": {
        "keywords": ["预防", "prevention", "疾病", "disease", "免疫"],
        "sources": [
            "https://www.cdc.gov",
            "https://www.who.int"
        ]
    },
    "运动健身": {
        "keywords": ["运动", "健身", "exercise", "fitness", "锻炼"],
        "sources": [
            "https://www.acefitness.org"
        ]
    },
    "心理健康": {
        "keywords": ["心理", "mental health", "心理健康", "情绪"],
        "sources": [
            "https://www.mentalhealth.gov"
        ]
    }
}

# 学术搜索源
ACADEMIC_SOURCES = {
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov",
    "Google Scholar": "https://scholar.google.com",
    "ResearchGate": "https://www.researchgate.net"
}

# 中文健康网站
CHINESE_SOURCES = {
    "丁香医生": "https://dxy.com",
    "好大夫在线": "https://www.haodf.com",
    "春雨医生": "https://www.chunyuyisheng.com"
}

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# 抓取配置
SCRAPER_CONFIG = {
    'timeout': 10,
    'max_retries': 3,
    'delay_between_requests': 2,
    'max_articles_per_category': 50,
    'enable_selenium': False  # 是否使用 Selenium 处理动态页面
}

# 导出配置
EXPORT_CONFIG = {
    'output_dir': 'scraped_data',
    'formats': ['csv', 'json', 'txt', 'excel']
}

# 数据库配置（可选）
DATABASE_CONFIG = {
    'enabled': False,
    'type': 'sqlite',
    'name': 'health_content.db'
}
