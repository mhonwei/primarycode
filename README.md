# 📚 电子教材实时更新系统 Demo

一个基于 WebSocket 的实时更新电子教材系统,支持教师端编辑内容后自动推送给订阅的学生。

## ✨ 核心功能

### 学生端功能
- 📖 浏览教材章节目录
- ✅ 选择性订阅感兴趣的章节
- 🔄 实时接收内容更新
- 💡 内容自动刷新(无需手动刷新页面)
- 📊 显示章节版本号
- 🔌 实时连接状态显示

### 教师端功能
- ✏️ 可视化编辑章节内容
- ➕ 添加/删除内容块(文本、代码)
- 🔀 调整内容块顺序
- 💾 一键保存并推送更新
- 📝 创建新章节
- 📡 自动通知所有订阅学生

## 🏗️ 技术架构

### 后端
- **Node.js + Express**: REST API 服务器
- **Socket.io**: WebSocket 实时通信
- **内存存储**: 演示用轻量级数据存储

### 前端
- **原生 JavaScript**: 无框架依赖
- **Socket.io-client**: 实时通信客户端
- **Marked.js**: Markdown 渲染
- **Highlight.js**: 代码高亮

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动服务器

```bash
npm start
```

或使用开发模式(支持热重载):

```bash
npm run dev
```

### 3. 访问系统

服务器启动后,在浏览器中访问:

- **学生阅读器**: http://localhost:3000/student.html
- **教师管理端**: http://localhost:3000/teacher.html

## 📖 使用指南

### 学生端使用流程

1. 打开学生阅读器页面
2. 从左侧章节列表中勾选感兴趣的章节(订阅)
3. 点击章节标题查看内容
4. 当教师更新内容时,会自动收到通知并刷新显示

### 教师端使用流程

1. 打开教师管理端页面
2. 从左侧列表选择要编辑的章节
3. 编辑内容块:
   - 修改文本/代码内容
   - 添加新的内容块
   - 调整内容块顺序
   - 删除不需要的内容块
4. 点击"保存并推送"按钮
5. 系统自动推送更新给所有订阅该章节的学生

## 🎯 实时更新演示步骤

1. 同时打开两个浏览器窗口:
   - 窗口A: 学生阅读器
   - 窗口B: 教师管理端

2. 在学生端订阅某个章节(如"第一章")

3. 在教师端编辑该章节内容并保存

4. 观察学生端自动显示更新通知并刷新内容

## 📁 项目结构

```
primarycode/
├── server/
│   └── index.js          # 后端服务器(Express + Socket.io)
├── public/
│   ├── student.html      # 学生阅读器界面
│   └── teacher.html      # 教师管理端界面
├── package.json          # 项目配置
├── .gitignore           # Git 忽略文件
└── README.md            # 项目说明
```

## 🔧 主要技术实现

### 实时推送机制

```javascript
// 服务端推送更新
io.to(`chapter:${chapterId}`).emit('content-update', updateEvent);

// 客户端接收更新
socket.on('content-update', (event) => {
  // 自动刷新内容
  renderChapterContent(event.chapter);
});
```

### 订阅模式

学生可以选择性订阅章节,只接收自己关心的内容更新:

```javascript
// 订阅章节
socket.emit('subscribe-chapters', {
  textbookId: 'tb-001',
  chapterIds: ['ch-001', 'ch-002']
});
```

### 版本控制

每次更新都会自动递增版本号,便于追踪内容变更:

```
v1.0 → v1.1 → v1.2 ...
```

## 🌟 特色亮点

1. **零刷新更新**: 学生端无需刷新页面即可看到最新内容
2. **选择性订阅**: 学生可以只订阅感兴趣的章节
3. **实时状态显示**: 显示连接状态和更新通知
4. **可视化编辑**: 教师端提供友好的内容编辑界面
5. **支持多种内容**: 文本(Markdown)、代码块
6. **版本追踪**: 显示每个章节的版本信息

## 🔮 扩展方向

本 Demo 可以扩展为完整的生产系统:

1. **数据持久化**: 集成 PostgreSQL/MongoDB
2. **用户认证**: 添加登录/权限管理
3. **离线支持**: Service Worker + IndexedDB
4. **协作编辑**: 多人实时协作编辑
5. **历史版本**: 内容版本历史和回滚
6. **更多内容类型**: 图片、视频、交互式组件
7. **学习分析**: 学习进度追踪和数据分析
8. **移动端适配**: 响应式设计或原生 App

## 📝 开发说明

### 数据模型

当前使用内存存储,数据结构如下:

```javascript
textbook {
  id: string
  title: string
  chapters: [
    {
      id: string
      title: string
      content: [
        {
          type: 'text' | 'code'
          content: string
          version: string
        }
      ]
      version: string
    }
  ]
}
```

### API 接口

- `GET /api/textbooks` - 获取教材列表
- `GET /api/textbooks/:id` - 获取教材详情
- `GET /api/textbooks/:tbId/chapters/:chId` - 获取章节内容
- `PUT /api/textbooks/:tbId/chapters/:chId` - 更新章节(推送更新)
- `POST /api/textbooks/:tbId/chapters` - 新增章节

### WebSocket 事件

**客户端 → 服务器:**
- `subscribe-textbook` - 订阅教材
- `subscribe-chapters` - 订阅章节
- `unsubscribe` - 取消订阅

**服务器 → 客户端:**
- `content-update` - 内容更新通知
- `subscribed` - 订阅成功确认

## 📄 许可证

MIT License

## 👨‍💻 作者

mhonwei (hongweimo73@gmail.com)
