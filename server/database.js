const initSqlJs = require('sql.js');
const path = require('path');
const fs = require('fs');
const config = require('./config');

let dbWrapper = null;

/**
 * sql.js 兼容层 - 提供与 better-sqlite3 相同的 API
 * 这样其他文件的代码不需要修改
 */
class DatabaseWrapper {
  constructor(sqlDb, dbPath) {
    this.db = sqlDb;
    this.dbPath = dbPath;
    this._saveTimer = null;
  }

  exec(sql) {
    this.db.exec(sql);
    this._scheduleSave();
  }

  prepare(sql) {
    const self = this;

    return {
      run(...params) {
        const converted = convertParams(params);
        if (converted) {
          self.db.run(sql, converted);
        } else {
          self.db.run(sql);
        }
        self._scheduleSave();

        const changes = self.db.getRowsModified();
        const lastInsertRowid = self._getLastRowId();
        return { changes, lastInsertRowid };
      },

      get(...params) {
        let stmt;
        try {
          stmt = self.db.prepare(sql);
          const converted = convertParams(params);
          if (converted) stmt.bind(converted);

          if (stmt.step()) {
            return stmt.getAsObject();
          }
          return undefined;
        } finally {
          if (stmt) stmt.free();
        }
      },

      all(...params) {
        let stmt;
        try {
          stmt = self.db.prepare(sql);
          const converted = convertParams(params);
          if (converted) stmt.bind(converted);

          const results = [];
          while (stmt.step()) {
            results.push(stmt.getAsObject());
          }
          return results;
        } finally {
          if (stmt) stmt.free();
        }
      },
    };
  }

  pragma() {
    // sql.js 不支持 pragma，忽略
  }

  _getLastRowId() {
    const stmt = this.db.prepare('SELECT last_insert_rowid() as id');
    let id = 0;
    if (stmt.step()) {
      id = stmt.getAsObject().id;
    }
    stmt.free();
    return id;
  }

  _scheduleSave() {
    if (this._saveTimer) clearTimeout(this._saveTimer);
    this._saveTimer = setTimeout(() => this._save(), 200);
  }

  _save() {
    try {
      const data = this.db.export();
      fs.writeFileSync(this.dbPath, Buffer.from(data));
    } catch (err) {
      console.error('[DB] Save error:', err.message);
    }
  }

  close() {
    if (this._saveTimer) clearTimeout(this._saveTimer);
    this._save();
    this.db.close();
    dbWrapper = null;
  }
}

/**
 * 转换参数格式
 * better-sqlite3: .run(val1, val2) 或 .run({name: val})
 * sql.js: .bind([val1, val2]) 或 .bind({"@name": val})
 */
function convertParams(params) {
  if (params.length === 0) return null;

  // 单个对象参数 → 命名参数
  if (
    params.length === 1 &&
    typeof params[0] === 'object' &&
    params[0] !== null &&
    !Array.isArray(params[0])
  ) {
    const obj = params[0];
    const converted = {};
    for (const [key, value] of Object.entries(obj)) {
      const paramKey = key.startsWith('@') || key.startsWith('$') || key.startsWith(':')
        ? key
        : `@${key}`;
      converted[paramKey] = value === undefined ? null : value;
    }
    return converted;
  }

  // 位置参数
  return params.map((v) => (v === undefined ? null : v));
}

/**
 * 初始化数据库（异步，启动时调用一次）
 */
async function initDatabase() {
  if (dbWrapper) return dbWrapper;

  const SQL = await initSqlJs();

  // 确保数据目录存在
  const dbDir = path.dirname(config.dbPath);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }

  // 加载已有数据库或创建新的
  let sqlDb;
  if (fs.existsSync(config.dbPath)) {
    const buffer = fs.readFileSync(config.dbPath);
    sqlDb = new SQL.Database(buffer);
  } else {
    sqlDb = new SQL.Database();
  }

  dbWrapper = new DatabaseWrapper(sqlDb, config.dbPath);

  // 初始化表结构
  initTables(dbWrapper);

  return dbWrapper;
}

/**
 * 获取数据库实例（同步，需先调用 initDatabase）
 */
function getDatabase() {
  if (!dbWrapper) {
    throw new Error('Database not initialized. Call initDatabase() first.');
  }
  return dbWrapper;
}

function initTables(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS articles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_name TEXT NOT NULL,
      source_url TEXT,
      original_title TEXT NOT NULL,
      original_content TEXT,
      original_link TEXT UNIQUE,
      original_language TEXT DEFAULT 'en',
      title TEXT,
      summary TEXT,
      content TEXT,
      category TEXT DEFAULT 'wellness',
      tags TEXT DEFAULT '[]',
      audience TEXT DEFAULT '["all"]',
      health_tips TEXT,
      status TEXT DEFAULT 'pending',
      published_at DATETIME,
      aggregated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      transformed_at DATETIME,
      view_count INTEGER DEFAULT 0,
      like_count INTEGER DEFAULT 0,
      share_count INTEGER DEFAULT 0,
      key_points TEXT DEFAULT '[]',
      credibility_score INTEGER DEFAULT 0,
      credibility_level TEXT DEFAULT 'medium',
      credibility_factors TEXT DEFAULT '[]'
    );

    CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
    CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
    CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
    CREATE INDEX IF NOT EXISTS idx_articles_aggregated ON articles(aggregated_at DESC);

    CREATE TABLE IF NOT EXISTS favorites (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      article_id INTEGER NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (article_id) REFERENCES articles(id),
      UNIQUE(user_id, article_id)
    );

    CREATE TABLE IF NOT EXISTS reading_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      article_id INTEGER NOT NULL,
      read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      read_duration INTEGER DEFAULT 0,
      FOREIGN KEY (article_id) REFERENCES articles(id)
    );

    CREATE TABLE IF NOT EXISTS aggregation_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_name TEXT NOT NULL,
      articles_found INTEGER DEFAULT 0,
      articles_added INTEGER DEFAULT 0,
      errors TEXT,
      started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      finished_at DATETIME
    );

    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE,
      phone TEXT UNIQUE,
      nickname TEXT DEFAULT '健康达人',
      password TEXT,
      membership TEXT DEFAULT 'free',
      font_size TEXT DEFAULT 'large',
      interests TEXT DEFAULT '[]',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      last_login DATETIME
    );
  `);

  // 为已有数据库添加新列（如果不存在则添加，存在则忽略错误）
  const alterStatements = [
    "ALTER TABLE articles ADD COLUMN key_points TEXT DEFAULT '[]'",
    "ALTER TABLE articles ADD COLUMN credibility_score INTEGER DEFAULT 0",
    "ALTER TABLE articles ADD COLUMN credibility_level TEXT DEFAULT 'medium'",
    "ALTER TABLE articles ADD COLUMN credibility_factors TEXT DEFAULT '[]'",
    "ALTER TABLE users ADD COLUMN username TEXT UNIQUE",
  ];

  for (const sql of alterStatements) {
    try {
      db.exec(sql);
    } catch (e) {
      // Column already exists, ignore
    }
  }
}

function closeDatabase() {
  if (dbWrapper) {
    dbWrapper.close();
    dbWrapper = null;
  }
}

module.exports = { initDatabase, getDatabase, closeDatabase };
