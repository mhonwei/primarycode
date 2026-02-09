# 健康资讯聚合平台

每日精选健康、养生、科学研究资讯，面向中老年人及青年人群提供科学可靠的健康信息服务。

支持 Web 移动端访问和微信小程序部署。

## 功能特性

- **智能采集**: 定时从多个权威健康/科学 RSS 源自动采集最新资讯
- **内容转换**: 将专业医学内容转换为通俗易懂的中文健康科普
- **智能分类**: 自动识别文章所属分类（医学研究、饮食营养、运动健身、疾病预防等）
- **受众识别**: 自动标注适合中老年人或青年人的内容
- **健康提示**: 每篇文章附带实用健康小贴士
- **字体调节**: 支持大/中/小三档字号，方便中老年人阅读
- **移动适配**: 移动优先的响应式设计，适配手机和平板
- **微信小程序**: 提供完整的微信小程序版本

## 内容分类

| 分类 | 说明 |
|------|------|
| 医学研究 | 最新医学科研成果 |
| 饮食营养 | 科学饮食与营养指导 |
| 养生保健 | 日常养生与保健知识 |
| 运动健身 | 科学运动与健身指导 |
| 疾病预防 | 疾病预防与早期筛查 |
| 心理健康 | 心理健康与情绪管理 |
| 康复护理 | 疾病康复与护理指导 |
| 公共卫生 | 公共卫生与健康政策 |
| 老年健康 | 中老年人健康管理 |
| 中医养生 | 传统中医与养生智慧 |

## 技术架构

```
health-news-aggregator/
├── server/                    # 后端服务
│   ├── index.js               # 服务入口
│   ├── config.js              # 配置文件
│   ├── database.js            # SQLite 数据库
│   ├── services/
│   │   ├── aggregator.js      # RSS 新闻采集服务
│   │   ├── transformer.js     # 内容转换服务（专业→科普）
│   │   └── scheduler.js       # 定时任务调度
│   ├── routes/
│   │   ├── articles.js        # 文章 API
│   │   ├── categories.js      # 分类 API
│   │   └── admin.js           # 管理 API
│   ├── scripts/
│   │   └── run-aggregation.js # 手动采集脚本
│   └── tests/
│       └── test.js            # 单元测试
├── client/                    # Web 前端（移动端优先）
│   ├── index.html             # 主页面
│   ├── css/style.css          # 响应式样式
│   └── js/
│       ├── api.js             # API 客户端
│       └── app.js             # 前端应用逻辑
└── miniprogram/               # 微信小程序
    ├── app.js / app.json      # 小程序入口
    └── pages/                 # 小程序页面
        ├── index/             # 首页
        ├── article/           # 文章详情
        ├── categories/        # 分类
        ├── trending/          # 热门
        └── profile/           # 个人中心
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动服务

```bash
# 启动服务器（含定时采集）
npm start

# 手动触发一次采集
npm run aggregate
```

服务启动后访问 `http://localhost:3000` 即可看到移动端界面。

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/articles` | 文章列表（支持分页、分类、搜索） |
| GET | `/api/articles/:id` | 文章详情 |
| POST | `/api/articles/:id/like` | 点赞 |
| POST | `/api/articles/:id/share` | 分享 |
| GET | `/api/categories` | 分类列表 |
| GET | `/api/admin/stats` | 系统统计 |
| POST | `/api/admin/aggregate` | 手动触发采集 |
| GET | `/api/health` | 健康检查 |

**查询参数示例:**
```
GET /api/articles?page=1&limit=20&category=nutrition&search=维生素&sort=popular
```

## 微信小程序部署

1. 在 `miniprogram/app.js` 中将 `apiBaseUrl` 改为你的服务器实际地址
2. 使用微信开发者工具打开 `miniprogram/` 目录
3. 配置小程序 AppID
4. 在小程序后台将服务器域名添加到请求合法域名列表
5. 上传并提交审核

## 数据源

默认配置了以下权威健康信息源（RSS）：

- Medical News Today
- WHO News（世界卫生组织）
- Harvard Health Blog（哈佛健康博客）
- ScienceDaily Health
- NIH Research Matters（美国国立卫生研究院）
- Nature Medicine（自然医学）
- WebMD Health

可在 `server/config.js` 中添加更多 RSS 源。

## 扩展建议

- **AI 翻译**: 接入翻译 API（如百度翻译、DeepL）实现高质量中英翻译
- **AI 改写**: 接入大语言模型 API（如 Claude、文心一言）进行内容适老化改写
- **中文源**: 添加国内健康资讯 RSS 源（丁香医生、健康报等）
- **推送通知**: 接入微信模板消息或邮件推送每日健康精选
- **用户系统**: 添加微信登录，实现个性化推荐
- **语音朗读**: 接入 TTS 服务，方便视力不佳的老年人收听

## 运行测试

```bash
npm test
```
