const express = require('express');
const cors = require('cors');
const path = require('path');
const config = require('./config');
const { getDatabase, closeDatabase } = require('./database');
const { startScheduler, stopScheduler } = require('./services/scheduler');
const articlesRouter = require('./routes/articles');
const categoriesRouter = require('./routes/categories');
const adminRouter = require('./routes/admin');

const app = express();

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 静态文件服务（前端页面）
app.use(express.static(path.join(__dirname, '..', 'client')));

// API 路由
app.use('/api/articles', articlesRouter);
app.use('/api/categories', categoriesRouter);
app.use('/api/admin', adminRouter);

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    message: '健康资讯聚合服务运行中',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  });
});

// SPA 前端路由回退
app.get('*', (req, res) => {
  if (!req.path.startsWith('/api/')) {
    res.sendFile(path.join(__dirname, '..', 'client', 'index.html'));
  }
});

// 错误处理中间件
app.use((err, req, res, _next) => {
  console.error('[错误]', err.message);
  res.status(500).json({
    success: false,
    message: '服务器内部错误',
  });
});

// 启动服务器
function start() {
  // 初始化数据库
  getDatabase();
  console.log('[数据库] 初始化完成');

  // 启动定时任务
  startScheduler();

  // 启动 HTTP 服务
  app.listen(config.port, config.host, () => {
    console.log(`\n${'='.repeat(50)}`);
    console.log('  健康资讯聚合平台 v1.0.0');
    console.log(`${'='.repeat(50)}`);
    console.log(`  服务地址: http://${config.host}:${config.port}`);
    console.log(`  API 文档: http://${config.host}:${config.port}/api/health`);
    console.log(`  管理接口: http://${config.host}:${config.port}/api/admin/stats`);
    console.log(`${'='.repeat(50)}\n`);
  });
}

// 优雅关闭
process.on('SIGINT', () => {
  console.log('\n[系统] 正在关闭服务...');
  stopScheduler();
  closeDatabase();
  process.exit(0);
});

process.on('SIGTERM', () => {
  stopScheduler();
  closeDatabase();
  process.exit(0);
});

start();

module.exports = app;
