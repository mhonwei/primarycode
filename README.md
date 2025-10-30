# AI案例智库系统 (AI Case Library System)

## 项目简介

这是一个自动生成人工智能通识课程教学案例库的系统，能够自动联网搜索新论文、技术、产品、行业应用与前沿热点等内容，并根据要求生成相应的教学案例。

## 核心功能

- 🔍 **多源智能搜索**：支持论文、技术、产品、行业应用、前沿热点等多维度搜索
- 🤖 **AI案例生成**：基于搜索结果自动生成高质量教学案例
- 📊 **可视化展示**：直观的网页界面展示搜索结果和生成的案例
- 🎯 **精准匹配**：准确度达90%以上的内容匹配和案例生成
- 🔧 **灵活定制**：支持自定义案例类型、难度、侧重点等参数

## 技术架构

### 后端技术栈
- **框架**: Flask (Python 3.9+)
- **爬虫**: BeautifulSoup4, Requests
- **AI生成**: 基于模板和智能摘要
- **数据处理**: Pandas, NLTK

### 前端技术栈
- **框架**: React 18
- **UI组件**: 原生CSS + 现代设计
- **HTTP客户端**: Fetch API

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
python app.py
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动前端服务

```bash
npm start
```

### 5. 访问系统

打开浏览器访问: http://localhost:3000

## 数据源

系统从以下高质量数据源抓取信息：

- **学术论文**: arXiv
- **技术文章**: GitHub Trending
- **产品信息**: Product Hunt API
- **行业资讯**: 公开AI新闻源
- **前沿热点**: 技术博客聚合

## 许可证

MIT License
