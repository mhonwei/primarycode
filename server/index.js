const express = require('express');
const http = require('http');
const socketIO = require('socket.io');
const cors = require('cors');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIO(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// 内存数据存储 (演示用)
const textbooks = {
  'tb-001': {
    id: 'tb-001',
    title: 'JavaScript 基础教程',
    description: '从零开始学习 JavaScript',
    version: '1.0.0',
    chapters: [
      {
        id: 'ch-001',
        title: '第一章：JavaScript 简介',
        order: 1,
        content: [
          {
            id: 'cb-001',
            type: 'text',
            content: '# JavaScript 简介\n\nJavaScript 是一种轻量级的编程语言,主要用于网页开发。它是 Web 的三大核心技术之一。',
            version: '1.0'
          },
          {
            id: 'cb-002',
            type: 'code',
            content: 'console.log("Hello, World!");',
            language: 'javascript',
            version: '1.0'
          }
        ],
        tags: ['基础', '入门'],
        version: '1.0'
      },
      {
        id: 'ch-002',
        title: '第二章：变量与数据类型',
        order: 2,
        content: [
          {
            id: 'cb-003',
            type: 'text',
            content: '# 变量与数据类型\n\nJavaScript 中有多种数据类型:\n- String (字符串)\n- Number (数字)\n- Boolean (布尔值)\n- Object (对象)\n- Array (数组)',
            version: '1.0'
          },
          {
            id: 'cb-004',
            type: 'code',
            content: 'let name = "张三";\nlet age = 25;\nlet isStudent = true;',
            language: 'javascript',
            version: '1.0'
          }
        ],
        tags: ['基础', '数据类型'],
        version: '1.0'
      },
      {
        id: 'ch-003',
        title: '第三章：函数',
        order: 3,
        content: [
          {
            id: 'cb-005',
            type: 'text',
            content: '# 函数\n\n函数是可重复使用的代码块。JavaScript 中定义函数的方式有多种。',
            version: '1.0'
          },
          {
            id: 'cb-006',
            type: 'code',
            content: 'function greet(name) {\n  return `你好, ${name}!`;\n}\n\nconst greet2 = (name) => `你好, ${name}!`;',
            language: 'javascript',
            version: '1.0'
          }
        ],
        tags: ['基础', '函数'],
        version: '1.0'
      }
    ]
  }
};

// 用户订阅信息
const userSubscriptions = new Map();

// API 路由

// 获取所有教材列表
app.get('/api/textbooks', (req, res) => {
  const list = Object.values(textbooks).map(tb => ({
    id: tb.id,
    title: tb.title,
    description: tb.description,
    version: tb.version,
    chapterCount: tb.chapters.length
  }));
  res.json(list);
});

// 获取教材详情
app.get('/api/textbooks/:id', (req, res) => {
  const textbook = textbooks[req.params.id];
  if (!textbook) {
    return res.status(404).json({ error: '教材不存在' });
  }
  res.json(textbook);
});

// 获取特定章节
app.get('/api/textbooks/:tbId/chapters/:chId', (req, res) => {
  const textbook = textbooks[req.params.tbId];
  if (!textbook) {
    return res.status(404).json({ error: '教材不存在' });
  }

  const chapter = textbook.chapters.find(ch => ch.id === req.params.chId);
  if (!chapter) {
    return res.status(404).json({ error: '章节不存在' });
  }

  res.json(chapter);
});

// 更新章节内容 (教师功能)
app.put('/api/textbooks/:tbId/chapters/:chId', (req, res) => {
  const textbook = textbooks[req.params.tbId];
  if (!textbook) {
    return res.status(404).json({ error: '教材不存在' });
  }

  const chapterIndex = textbook.chapters.findIndex(ch => ch.id === req.params.chId);
  if (chapterIndex === -1) {
    return res.status(404).json({ error: '章节不存在' });
  }

  const { content } = req.body;
  const oldVersion = textbook.chapters[chapterIndex].version;
  const newVersion = incrementVersion(oldVersion);

  // 更新章节内容
  textbook.chapters[chapterIndex].content = content;
  textbook.chapters[chapterIndex].version = newVersion;
  textbook.chapters[chapterIndex].updatedAt = new Date();

  // 通过 WebSocket 推送更新事件
  const updateEvent = {
    type: 'chapter_updated',
    textbookId: req.params.tbId,
    chapterId: req.params.chId,
    chapter: textbook.chapters[chapterIndex],
    timestamp: new Date()
  };

  // 推送给所有订阅此章节的用户
  io.to(`chapter:${req.params.chId}`).emit('content-update', updateEvent);

  console.log(`📝 章节更新: ${textbook.chapters[chapterIndex].title} (v${oldVersion} → v${newVersion})`);
  console.log(`   推送给房间: chapter:${req.params.chId}`);

  res.json({
    success: true,
    chapter: textbook.chapters[chapterIndex],
    event: updateEvent
  });
});

// 添加新章节
app.post('/api/textbooks/:tbId/chapters', (req, res) => {
  const textbook = textbooks[req.params.tbId];
  if (!textbook) {
    return res.status(404).json({ error: '教材不存在' });
  }

  const { title, content, tags } = req.body;
  const newChapter = {
    id: `ch-${Date.now()}`,
    title,
    order: textbook.chapters.length + 1,
    content: content || [],
    tags: tags || [],
    version: '1.0',
    createdAt: new Date()
  };

  textbook.chapters.push(newChapter);

  // 推送新章节事件
  const updateEvent = {
    type: 'chapter_added',
    textbookId: req.params.tbId,
    chapter: newChapter,
    timestamp: new Date()
  };

  io.to(`textbook:${req.params.tbId}`).emit('content-update', updateEvent);

  console.log(`➕ 新增章节: ${newChapter.title}`);

  res.json({
    success: true,
    chapter: newChapter,
    event: updateEvent
  });
});

// WebSocket 连接处理
io.on('connection', (socket) => {
  console.log(`🔌 客户端连接: ${socket.id}`);

  // 订阅教材
  socket.on('subscribe-textbook', (textbookId) => {
    socket.join(`textbook:${textbookId}`);
    console.log(`📚 ${socket.id} 订阅教材: ${textbookId}`);

    // 记录订阅信息
    if (!userSubscriptions.has(socket.id)) {
      userSubscriptions.set(socket.id, {
        textbooks: new Set(),
        chapters: new Set()
      });
    }
    userSubscriptions.get(socket.id).textbooks.add(textbookId);

    socket.emit('subscribed', {
      type: 'textbook',
      id: textbookId,
      timestamp: new Date()
    });
  });

  // 订阅章节
  socket.on('subscribe-chapters', ({ textbookId, chapterIds }) => {
    chapterIds.forEach(chapterId => {
      socket.join(`chapter:${chapterId}`);
      console.log(`📖 ${socket.id} 订阅章节: ${chapterId}`);

      if (!userSubscriptions.has(socket.id)) {
        userSubscriptions.set(socket.id, {
          textbooks: new Set(),
          chapters: new Set()
        });
      }
      userSubscriptions.get(socket.id).chapters.add(chapterId);
    });

    socket.emit('subscribed', {
      type: 'chapters',
      textbookId,
      chapterIds,
      timestamp: new Date()
    });
  });

  // 取消订阅
  socket.on('unsubscribe', ({ type, id }) => {
    if (type === 'textbook') {
      socket.leave(`textbook:${id}`);
      console.log(`🚫 ${socket.id} 取消订阅教材: ${id}`);
    } else if (type === 'chapter') {
      socket.leave(`chapter:${id}`);
      console.log(`🚫 ${socket.id} 取消订阅章节: ${id}`);
    }
  });

  // 获取当前订阅信息
  socket.on('get-subscriptions', () => {
    const subs = userSubscriptions.get(socket.id) || { textbooks: new Set(), chapters: new Set() };
    socket.emit('subscriptions-info', {
      textbooks: Array.from(subs.textbooks),
      chapters: Array.from(subs.chapters)
    });
  });

  // 断开连接
  socket.on('disconnect', () => {
    console.log(`❌ 客户端断开: ${socket.id}`);
    userSubscriptions.delete(socket.id);
  });
});

// 辅助函数：版本号递增
function incrementVersion(version) {
  const parts = version.split('.');
  parts[parts.length - 1] = parseInt(parts[parts.length - 1]) + 1;
  return parts.join('.');
}

// 启动服务器
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════════╗
║   📚 电子教材实时更新系统 Demo 已启动!            ║
╠════════════════════════════════════════════════════╣
║   服务器地址: http://localhost:${PORT}
║   学生界面:   http://localhost:${PORT}/student.html
║   教师界面:   http://localhost:${PORT}/teacher.html
╚════════════════════════════════════════════════════╝
  `);
});
