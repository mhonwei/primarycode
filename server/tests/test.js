const { describe, it, before, after } = require('node:test');
const assert = require('node:assert');
const path = require('path');

// 设置测试数据库路径
process.env.DB_PATH = path.join(__dirname, '..', '..', 'data', 'test_health_news.db');

const { initDatabase, getDatabase, closeDatabase } = require('../database');
const {
  translateTitle,
  translateContent,
  generateChineseSummary,
  detectCategory,
  detectAudience,
  extractTags,
  extractHealthTips,
  transformArticle,
} = require('../services/transformer');

// 在所有测试前初始化数据库
before(async () => {
  await initDatabase();
});

describe('Database', () => {
  it('should initialize database successfully', () => {
    const db = getDatabase();
    assert.ok(db, 'Database should be initialized');

    // 验证表是否创建
    const tables = db
      .prepare("SELECT name FROM sqlite_master WHERE type='table'")
      .all()
      .map((t) => t.name);

    assert.ok(tables.includes('articles'), 'articles table should exist');
    assert.ok(tables.includes('favorites'), 'favorites table should exist');
    assert.ok(tables.includes('reading_history'), 'reading_history table should exist');
    assert.ok(tables.includes('aggregation_logs'), 'aggregation_logs table should exist');
  });

  it('should insert and query articles', () => {
    const db = getDatabase();

    const result = db
      .prepare(
        `INSERT INTO articles (source_name, original_title, original_content, original_link, category, status)
       VALUES (?, ?, ?, ?, ?, ?)`
      )
      .run(
        'Test Source',
        'Test Article About Diabetes',
        'A new study shows that exercise can help manage diabetes.',
        'https://example.com/test-article-1',
        'medical_research',
        'pending'
      );

    assert.ok(result.lastInsertRowid > 0, 'Article should be inserted');

    const article = db.prepare('SELECT * FROM articles WHERE id = ?').get(result.lastInsertRowid);
    assert.strictEqual(article.source_name, 'Test Source');
    assert.strictEqual(article.status, 'pending');
  });
});

describe('Content Transformer', () => {
  it('should transform health-related titles', async () => {
    const result = await translateTitle('New Study Shows diabetes Treatment Breakthrough');
    assert.ok(result.includes('糖尿病'), 'Should translate diabetes to Chinese');
  });

  it('should detect medical research category', () => {
    const category = detectCategory(
      'New clinical trial results published',
      'Researchers found a new breakthrough in cancer treatment'
    );
    assert.strictEqual(category, 'medical_research');
  });

  it('should detect nutrition category', () => {
    const category = detectCategory(
      'Best foods for heart health',
      'Diet rich in fiber and vitamins can improve health'
    );
    assert.strictEqual(category, 'nutrition');
  });

  it('should detect elderly audience', () => {
    const audience = detectAudience(
      'Fall prevention for elderly',
      'Senior citizens should be careful about osteoporosis'
    );
    assert.ok(audience.includes('elderly'), 'Should detect elderly audience');
  });

  it('should extract tags from content', () => {
    const tags = extractTags(
      'Diabetes and hypertension study',
      'Research on diabetes and high blood pressure treatment with exercise'
    );
    assert.ok(tags.length > 0, 'Should extract at least one tag');
    assert.ok(tags.includes('糖尿病'), 'Should include diabetes tag in Chinese');
  });

  it('should generate a summary from content', async () => {
    const content =
      'This is a very important health study. It shows that regular exercise reduces the risk of heart disease. Walking 30 minutes daily is recommended.';
    const summary = await generateChineseSummary('Health Study', content);
    assert.ok(summary.length > 0, 'Summary should not be empty');
    assert.ok(summary.length <= 600, 'Summary should be within length limits');
  });

  it('should extract health tips based on category', () => {
    const tips = extractHealthTips('Exercise and fitness content', 'fitness');
    assert.ok(tips.length > 0, 'Should return health tips');
    assert.ok(
      tips.some((t) => t.includes('免责声明')),
      'Should include disclaimer'
    );
  });

  it('should transform a complete article', async () => {
    const article = {
      id: 1,
      original_title: 'New diabetes research shows promising results',
      original_content:
        'A clinical trial has demonstrated that a new treatment can significantly lower blood pressure in patients with diabetes.',
      category: 'medical_research',
    };

    const result = await transformArticle(article);
    assert.ok(result.title, 'Should have a title');
    assert.ok(result.summary, 'Should have a summary');
    assert.ok(result.content, 'Should have content');
    assert.ok(result.category, 'Should have a category');
    assert.ok(result.tags, 'Should have tags');
    assert.ok(result.health_tips, 'Should have health tips');
  });
});

// 清理测试数据库
after(() => {
  closeDatabase();
  const fs = require('fs');
  const testDbPath = path.join(__dirname, '..', '..', 'data', 'test_health_news.db');
  try {
    fs.unlinkSync(testDbPath);
  } catch {
    // 文件可能不存在
  }
});
