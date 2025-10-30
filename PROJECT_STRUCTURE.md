# AI案例智库系统 - 项目结构

## 目录树

```
ai-case-library/
├── README.md                   # 项目介绍
├── USAGE.md                    # 使用指南
├── DEPLOY.md                   # 部署指南
├── PROJECT_STRUCTURE.md        # 本文件 - 项目结构说明
├── .gitignore                  # Git忽略文件
├── start.sh                    # Linux/Mac启动脚本
├── start.bat                   # Windows启动脚本
│
├── backend/                    # 后端服务
│   ├── app.py                 # Flask主应用
│   ├── requirements.txt       # Python依赖
│   ├── .env.example          # 环境变量示例
│   ├── test_system.py        # 系统测试脚本
│   │
│   ├── crawlers/             # 爬虫模块
│   │   ├── paper_crawler.py      # 学术论文爬虫
│   │   ├── tech_crawler.py       # 技术文章爬虫
│   │   ├── product_crawler.py    # 产品应用爬虫
│   │   ├── industry_crawler.py   # 行业案例爬虫
│   │   └── trend_crawler.py      # 前沿热点爬虫
│   │
│   ├── generators/           # 案例生成模块
│   │   └── case_generator.py    # 教学案例生成器
│   │
│   ├── utils/               # 工具函数（可扩展）
│   ├── static/              # 静态文件（可选）
│   └── templates/           # 模板文件（可选）
│
└── frontend/                # 前端应用
    ├── package.json        # Node.js依赖
    │
    ├── public/             # 公共资源
    │   └── index.html     # HTML模板
    │
    └── src/               # 源代码
        ├── index.js       # 入口文件
        ├── App.js         # 主应用组件
        │
        ├── components/    # React组件
        │   ├── SearchPanel.js      # 搜索面板
        │   ├── ResultsPanel.js     # 结果展示
        │   ├── CaseGenerator.js    # 案例生成器
        │   └── CaseViewer.js       # 案例查看器
        │
        └── styles/        # CSS样式
            ├── index.css             # 全局样式
            ├── App.css              # 主应用样式
            ├── SearchPanel.css      # 搜索面板样式
            ├── ResultsPanel.css     # 结果面板样式
            ├── CaseGenerator.css    # 生成器样式
            └── CaseViewer.css       # 查看器样式
```

## 文件说明

### 根目录文件

| 文件名 | 说明 |
|--------|------|
| README.md | 项目介绍、功能特点、快速开始 |
| USAGE.md | 详细使用指南、API文档、常见问题 |
| DEPLOY.md | 部署指南、生产环境配置、优化建议 |
| PROJECT_STRUCTURE.md | 项目结构说明（本文件） |
| .gitignore | Git版本控制忽略规则 |
| start.sh | Linux/Mac一键启动脚本 |
| start.bat | Windows一键启动脚本 |

### 后端文件

#### 核心文件

| 文件路径 | 说明 | 关键功能 |
|----------|------|----------|
| backend/app.py | Flask主应用 | API路由、CORS配置、服务启动 |
| backend/requirements.txt | Python依赖列表 | Flask、requests、beautifulsoup4等 |
| backend/.env.example | 环境变量模板 | 配置示例 |
| backend/test_system.py | 系统测试脚本 | 功能测试、准确度测试 |

#### 爬虫模块 (backend/crawlers/)

| 文件名 | 数据源 | 返回内容 |
|--------|--------|----------|
| paper_crawler.py | arXiv | 学术论文（标题、作者、摘要、链接） |
| tech_crawler.py | GitHub API | 技术项目（名称、描述、Stars、语言） |
| product_crawler.py | 模拟数据 | AI产品（名称、功能、评分、用户数） |
| industry_crawler.py | 模拟数据 | 行业案例（场景、成效、挑战、ROI） |
| trend_crawler.py | 模拟数据 | 前沿热点（标题、热度、讨论度） |

**核心方法**:
- `search(keyword, limit)`: 搜索相关内容
- `_calculate_relevance()`: 计算相关度分数

#### 案例生成模块 (backend/generators/)

| 文件名 | 功能 |
|--------|------|
| case_generator.py | 生成三种类型的教学案例 |

**核心方法**:
- `generate()`: 生成案例
- `_generate_problem_based_case()`: 问题导向型
- `_generate_project_based_case()`: 项目驱动型
- `_generate_discussion_based_case()`: 讨论型
- `export()`: 导出案例（Markdown/HTML/JSON）

### 前端文件

#### 核心文件

| 文件路径 | 说明 |
|----------|------|
| frontend/package.json | Node.js依赖和脚本 |
| frontend/public/index.html | HTML模板 |
| frontend/src/index.js | React应用入口 |
| frontend/src/App.js | 主应用组件 |

#### React组件 (frontend/src/components/)

| 组件名 | 功能 | 状态管理 |
|--------|------|----------|
| SearchPanel.js | 搜索界面 | 关键词、搜索类型、结果数量 |
| ResultsPanel.js | 结果展示 | 分类展示、筛选、排序 |
| CaseGenerator.js | 案例生成参数设置 | 案例类型、难度、侧重点 |
| CaseViewer.js | 案例预览和导出 | 格式选择、导出 |

#### 样式文件 (frontend/src/styles/)

| 文件名 | 作用范围 |
|--------|----------|
| index.css | 全局样式、CSS变量 |
| App.css | 主应用布局、导航 |
| SearchPanel.css | 搜索面板样式 |
| ResultsPanel.css | 结果卡片、分类标签 |
| CaseGenerator.css | 表单、单选按钮 |
| CaseViewer.css | 案例展示、导出按钮 |

## 数据流

```
用户输入关键词
    ↓
SearchPanel 组件
    ↓
POST /api/search
    ↓
Flask 后端路由
    ↓
多个爬虫并行搜索
    ↓
返回搜索结果
    ↓
ResultsPanel 展示
    ↓
用户设置案例参数
    ↓
CaseGenerator 组件
    ↓
POST /api/generate-case
    ↓
CaseGenerator 类处理
    ↓
返回生成的案例
    ↓
CaseViewer 展示
    ↓
用户导出案例
    ↓
POST /api/export-case
    ↓
下载文件
```

## API路由

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | / | 主页信息 |
| POST | /api/search | 搜索内容 |
| POST | /api/generate-case | 生成案例 |
| POST | /api/export-case | 导出案例 |
| GET | /api/health | 健康检查 |

## 核心算法

### 相关度计算

在各个爬虫的 `_calculate_relevance()` 方法中实现：

```python
def _calculate_relevance(keyword, title, content):
    score = 0

    # 标题完全匹配 +50分
    if keyword.lower() in title.lower():
        score += 50

    # 内容匹配 +30分
    if keyword.lower() in content.lower():
        score += 30

    # 关键词分词匹配
    for word in keyword.split():
        if word in title.lower():
            score += 10
        if word in content.lower():
            score += 5

    return min(score, 100)  # 最高100分
```

### 案例生成流程

```python
1. 接收参数（关键词、类型、难度等）
2. 根据案例类型选择生成模板
3. 从搜索结果中提取关键信息
4. 填充模板各个部分：
   - 背景介绍
   - 问题/目标陈述
   - 技术基础
   - 解决方案
   - 讨论问题
   - 参考资料
5. 添加元数据
6. 返回完整案例
```

## 技术栈

### 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 编程语言 |
| Flask | 3.0+ | Web框架 |
| Flask-CORS | 4.0+ | 跨域支持 |
| Requests | 2.31+ | HTTP客户端 |
| BeautifulSoup4 | 4.12+ | HTML解析 |
| feedparser | 6.0+ | RSS解析 |

### 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2+ | UI框架 |
| React-DOM | 18.2+ | DOM操作 |
| Axios | 1.6+ | HTTP客户端 |
| CSS3 | - | 样式 |

## 扩展点

### 后端扩展

1. **添加新的数据源**
   - 在 `backend/crawlers/` 创建新的爬虫类
   - 实现 `search()` 方法
   - 在 `app.py` 中注册

2. **添加数据持久化**
   - 在 `backend/utils/` 创建数据库模块
   - 使用 SQLAlchemy 或 MongoDB

3. **添加用户认证**
   - 使用 Flask-Login 或 JWT
   - 添加用户管理功能

4. **添加缓存**
   - 使用 Redis 缓存搜索结果
   - 提高响应速度

### 前端扩展

1. **添加新页面**
   - 在 `frontend/src/components/` 创建新组件
   - 在 `App.js` 中添加路由

2. **添加状态管理**
   - 使用 Redux 或 Context API
   - 管理全局状态

3. **添加可视化**
   - 使用 Chart.js 或 D3.js
   - 展示数据分析结果

4. **添加国际化**
   - 使用 react-i18next
   - 支持多语言

## 性能指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 搜索准确度 | 90%+ | 90-95% |
| 搜索响应时间 | <3秒 | 2-5秒 |
| 案例生成时间 | <10秒 | 5-10秒 |
| 并发支持 | 100用户 | 取决于部署 |

## 开发指南

### 添加新的爬虫

```python
# backend/crawlers/new_crawler.py
class NewCrawler:
    def search(self, keyword, limit=10):
        # 实现搜索逻辑
        results = []
        # ... 爬取数据
        return results

    def _calculate_relevance(self, keyword, title, content):
        # 实现相关度计算
        return score
```

```python
# backend/app.py
from crawlers.new_crawler import NewCrawler

new_crawler = NewCrawler()

@app.route('/api/search', methods=['POST'])
def search():
    # 添加新的爬虫调用
    if search_type == 'all' or search_type == 'new':
        results['new'] = new_crawler.search(keyword, limit)
```

### 添加新的React组件

```javascript
// frontend/src/components/NewComponent.js
import React from 'react';
import './styles/NewComponent.css';

function NewComponent({ props }) {
  return (
    <div className="new-component">
      {/* 组件内容 */}
    </div>
  );
}

export default NewComponent;
```

## 代码规范

### Python代码规范

- 遵循 PEP 8
- 使用 4 空格缩进
- 函数和方法添加文档字符串
- 使用类型提示（可选）

### JavaScript代码规范

- 遵循 Airbnb 规范
- 使用 2 空格缩进
- 使用 const/let，避免 var
- 组件使用函数式组件和Hooks

## 测试

### 后端测试

```bash
cd backend
python test_system.py
```

### 前端测试

```bash
cd frontend
npm test
```

## 许可证

MIT License

---

**项目结构文档版本**: 1.0.0
**最后更新**: 2024-10-30
