const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');
const config = require('./config');

let db;

function getDatabase() {
  if (db) return db;

  // 确保数据目录存在
  const dbDir = path.dirname(config.dbPath);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }

  db = new Database(config.dbPath);

  // 启用 WAL 模式提升并发性能
  db.pragma('journal_mode = WAL');

  // 初始化表结构
  initTables(db);

  return db;
}

function initTables(db) {
  db.exec(`
    -- 文章表
    CREATE TABLE IF NOT EXISTS articles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_name TEXT NOT NULL,
      source_url TEXT,
      original_title TEXT NOT NULL,
      original_content TEXT,
      original_link TEXT UNIQUE,
      original_language TEXT DEFAULT 'en',

      -- 转换后的中文内容
      title TEXT,
      summary TEXT,
      content TEXT,

      -- 分类与标签
      category TEXT DEFAULT 'wellness',
      tags TEXT DEFAULT '[]',

      -- 适用人群标签
      audience TEXT DEFAULT '["all"]',

      -- 健康提示/实用建议
      health_tips TEXT,

      -- 状态管理
      status TEXT DEFAULT 'pending',

      -- 时间信息
      published_at DATETIME,
      aggregated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      transformed_at DATETIME,

      -- 阅读统计
      view_count INTEGER DEFAULT 0,
      like_count INTEGER DEFAULT 0,
      share_count INTEGER DEFAULT 0
    );

    -- 分类索引
    CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
    CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
    CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
    CREATE INDEX IF NOT EXISTS idx_articles_aggregated ON articles(aggregated_at DESC);

    -- 用户收藏表
    CREATE TABLE IF NOT EXISTS favorites (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      article_id INTEGER NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (article_id) REFERENCES articles(id),
      UNIQUE(user_id, article_id)
    );

    -- 阅读历史表
    CREATE TABLE IF NOT EXISTS reading_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      article_id INTEGER NOT NULL,
      read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      read_duration INTEGER DEFAULT 0,
      FOREIGN KEY (article_id) REFERENCES articles(id)
    );

    -- 采集日志表
    CREATE TABLE IF NOT EXISTS aggregation_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_name TEXT NOT NULL,
      articles_found INTEGER DEFAULT 0,
      articles_added INTEGER DEFAULT 0,
      errors TEXT,
      started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      finished_at DATETIME
    );
  `);
}

function closeDatabase() {
  if (db) {
    db.close();
    db = null;
  }
}

module.exports = { getDatabase, closeDatabase };
