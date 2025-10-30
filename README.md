# 健康内容网络爬虫系统

一个功能强大的健康内容网络爬虫系统，带有友好的图形用户界面，可以在 Windows 上运行。

## 功能特性

- **图形用户界面**: 基于 Tkinter 的直观易用界面
- **多种抓取模式**:
  - 快速抓取：按分类自动搜索和抓取内容
  - 自定义抓取：手动输入 URL 列表进行抓取
  - 学术搜索：搜索 PubMed 等学术数据库
- **内容分类**:
  - 健康管理
  - 饮食管理
  - 疾病预防
  - 运动健身
  - 心理健康
- **数据导出**: 支持 JSON、CSV、Excel、TXT 多种格式
- **实时进度显示**: 可视化的进度条和日志输出
- **数据统计**: 自动生成数据统计信息

## 系统要求

- Python 3.7 或更高版本
- Windows 操作系统（也可在 macOS 和 Linux 上运行）
- 网络连接

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/health-content-scraper.git
cd health-content-scraper
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python main.py
```

## 使用方法

### 快速抓取

1. 打开应用程序
2. 在"快速抓取"标签页中选择要抓取的内容分类
3. 设置每个分类要抓取的数量
4. 点击"开始抓取"按钮
5. 等待抓取完成

### 自定义抓取

1. 切换到"自定义抓取"标签页
2. 在文本框中输入要抓取的 URL 列表（每行一个）
3. 选择内容分类
4. 点击"开始抓取"按钮

### 学术搜索

1. 切换到"学术搜索"标签页
2. 输入搜索关键词（英文）
3. 设置结果数量
4. 点击"开始搜索"按钮

### 数据导出

1. 切换到"数据管理"标签页
2. 查看数据统计信息
3. 选择导出格式
4. 点击"导出数据"按钮
5. 数据将保存在 `scraped_data` 文件夹中

## 项目结构

```
health-content-scraper/
│
├── main.py                 # 主程序（GUI 界面）
├── scraper.py             # 网页爬虫模块
├── data_manager.py        # 数据管理模块
├── config.py              # 配置文件
├── requirements.txt       # Python 依赖包
├── README.md             # 说明文档
│
└── scraped_data/         # 输出文件夹（自动创建）
    ├── *.json            # JSON 格式数据
    ├── *.csv             # CSV 格式数据
    ├── *.xlsx            # Excel 格式数据
    └── *.txt             # TXT 格式数据
```

## 配置说明

可以在 `config.py` 文件中自定义以下设置：

- **内容分类**: 添加或修改内容分类及其关键词
- **数据源**: 配置要抓取的网站列表
- **抓取参数**: 设置超时时间、重试次数、请求延迟等
- **导出选项**: 配置输出目录和支持的导出格式

## 示例代码

### 命令行模式使用

如果你想在命令行中使用爬虫功能：

```python
from scraper import HealthContentScraper
from data_manager import DataManager

# 创建爬虫实例
scraper = HealthContentScraper()

# 抓取单个 URL
article = scraper.scrape_url("https://example.com/health-article", "健康管理")

# 批量抓取
urls = [
    "https://example.com/article1",
    "https://example.com/article2"
]
articles = scraper.scrape_urls(urls, "疾病预防")

# 保存数据
data_manager = DataManager()
data_manager.save_to_json(articles)
data_manager.save_to_csv(articles)
```

## 注意事项

1. **遵守网站规则**: 请遵守目标网站的 robots.txt 和使用条款
2. **请求频率**: 程序默认在请求之间有延迟，避免给服务器造成负担
3. **数据准确性**: 由于网站结构可能变化，抓取的数据可能需要人工校验
4. **法律合规**: 仅用于学习和研究目的，请勿用于商业用途

## 常见问题

### Q: 抓取失败怎么办？

A: 检查网络连接，确认目标网站可访问。某些网站可能有反爬虫机制，可以尝试：
- 增加请求延迟
- 使用不同的 User-Agent
- 启用 Selenium 模式处理动态页面

### Q: 如何添加新的数据源？

A: 在 `config.py` 文件中的相应分类下添加新的 URL：

```python
"健康管理": {
    "keywords": ["健康管理", "health management"],
    "sources": [
        "https://example.com",
        "https://new-source.com"  # 添加新源
    ]
}
```

### Q: 支持中文网站吗？

A: 支持！程序已配置了中文网站支持，可以正确处理中文内容。

## 依赖包说明

- `requests`: HTTP 请求库
- `beautifulsoup4`: HTML 解析库
- `lxml`: XML/HTML 解析器
- `selenium`: 用于处理动态网页（可选）
- `pandas`: 数据处理和导出
- `openpyxl`: Excel 文件支持

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/yourusername/health-content-scraper/issues)
- 邮箱: your.email@example.com

## 更新日志

### v1.0.0 (2025-10-30)

- 初始版本发布
- 实现基本的网页抓取功能
- 添加图形用户界面
- 支持多种数据导出格式
- 实现学术搜索功能

## 致谢

感谢所有为开源项目做出贡献的开发者！

---

**免责声明**: 本工具仅供学习和研究使用。使用者应遵守相关法律法规和网站使用条款，对使用本工具产生的任何后果自行负责。
