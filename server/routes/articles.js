const express = require('express');
const { getDatabase } = require('../database');
const config = require('../config');

const router = express.Router();

/**
 * GET /api/articles
 * 获取文章列表（支持分页、分类筛选、搜索）
 */
router.get('/', (req, res) => {
  const db = getDatabase();
  const {
    page = 1,
    limit = 20,
    category,
    search,
    audience,
    sort = 'latest',
  } = req.query;

  const pageNum = Math.max(1, parseInt(page, 10) || 1);
  const pageSize = Math.min(50, Math.max(1, parseInt(limit, 10) || 20));
  const offset = (pageNum - 1) * pageSize;

  let whereClause = "WHERE status = 'transformed'";
  const params = [];

  if (category) {
    whereClause += ' AND category = ?';
    params.push(category);
  }

  if (search) {
    whereClause += ' AND (title LIKE ? OR summary LIKE ? OR tags LIKE ?)';
    const searchTerm = `%${search}%`;
    params.push(searchTerm, searchTerm, searchTerm);
  }

  if (audience) {
    whereClause += ' AND audience LIKE ?';
    params.push(`%${audience}%`);
  }

  let orderClause;
  switch (sort) {
    case 'popular':
      orderClause = 'ORDER BY view_count DESC, published_at DESC';
      break;
    case 'liked':
      orderClause = 'ORDER BY like_count DESC, published_at DESC';
      break;
    default:
      orderClause = 'ORDER BY published_at DESC';
  }

  // 获取总数
  const countResult = db
    .prepare(`SELECT COUNT(*) as total FROM articles ${whereClause}`)
    .get(...params);

  // 获取文章列表
  const articles = db
    .prepare(
      `SELECT id, title, summary, category, tags, audience, health_tips,
              key_points, credibility_score, credibility_level, credibility_factors,
              published_at, view_count, like_count, share_count, source_name
       FROM articles ${whereClause} ${orderClause}
       LIMIT ? OFFSET ?`
    )
    .all(...params, pageSize, offset);

  // 解析 JSON 字段
  const parsedArticles = articles.map((article) => ({
    ...article,
    tags: safeJsonParse(article.tags, []),
    audience: safeJsonParse(article.audience, ['all']),
    health_tips: safeJsonParse(article.health_tips, []),
    key_points: safeJsonParse(article.key_points, []),
    credibility_factors: safeJsonParse(article.credibility_factors, []),
  }));

  res.json({
    success: true,
    data: {
      articles: parsedArticles,
      pagination: {
        page: pageNum,
        limit: pageSize,
        total: countResult.total,
        totalPages: Math.ceil(countResult.total / pageSize),
      },
    },
  });
});

/**
 * GET /api/articles/:id
 * 获取文章详情
 */
router.get('/:id', (req, res) => {
  const db = getDatabase();
  const { id } = req.params;

  const article = db.prepare('SELECT * FROM articles WHERE id = ?').get(id);

  if (!article) {
    return res.status(404).json({ success: false, message: '文章不存在' });
  }

  // 增加阅读计数
  db.prepare('UPDATE articles SET view_count = view_count + 1 WHERE id = ?').run(id);

  res.json({
    success: true,
    data: {
      ...article,
      tags: safeJsonParse(article.tags, []),
      audience: safeJsonParse(article.audience, ['all']),
      health_tips: safeJsonParse(article.health_tips, []),
      key_points: safeJsonParse(article.key_points, []),
      credibility_factors: safeJsonParse(article.credibility_factors, []),
      view_count: article.view_count + 1,
    },
  });
});

/**
 * POST /api/articles/:id/like
 * 点赞文章
 */
router.post('/:id/like', (req, res) => {
  const db = getDatabase();
  const { id } = req.params;

  const result = db
    .prepare('UPDATE articles SET like_count = like_count + 1 WHERE id = ?')
    .run(id);

  if (result.changes === 0) {
    return res.status(404).json({ success: false, message: '文章不存在' });
  }

  const article = db.prepare('SELECT like_count FROM articles WHERE id = ?').get(id);
  res.json({ success: true, data: { like_count: article.like_count } });
});

/**
 * POST /api/articles/:id/share
 * 分享文章
 */
router.post('/:id/share', (req, res) => {
  const db = getDatabase();
  const { id } = req.params;

  db.prepare('UPDATE articles SET share_count = share_count + 1 WHERE id = ?').run(id);
  res.json({ success: true, message: '分享成功' });
});

/**
 * GET /api/articles/category/:category
 * 按分类获取文章
 */
router.get('/category/:category', (req, res) => {
  const db = getDatabase();
  const { category } = req.params;
  const { page = 1, limit = 20 } = req.query;

  const pageNum = Math.max(1, parseInt(page, 10) || 1);
  const pageSize = Math.min(50, Math.max(1, parseInt(limit, 10) || 20));
  const offset = (pageNum - 1) * pageSize;

  const articles = db
    .prepare(
      `SELECT id, title, summary, category, tags, audience, health_tips,
              published_at, view_count, like_count, source_name
       FROM articles
       WHERE status = 'transformed' AND category = ?
       ORDER BY published_at DESC
       LIMIT ? OFFSET ?`
    )
    .all(category, pageSize, offset);

  const countResult = db
    .prepare(
      "SELECT COUNT(*) as total FROM articles WHERE status = 'transformed' AND category = ?"
    )
    .get(category);

  res.json({
    success: true,
    data: {
      articles: articles.map((a) => ({
        ...a,
        tags: safeJsonParse(a.tags, []),
        audience: safeJsonParse(a.audience, ['all']),
        health_tips: safeJsonParse(a.health_tips, []),
      })),
      pagination: {
        page: pageNum,
        limit: pageSize,
        total: countResult.total,
        totalPages: Math.ceil(countResult.total / pageSize),
      },
    },
  });
});

function safeJsonParse(str, defaultValue) {
  try {
    return JSON.parse(str);
  } catch {
    return defaultValue;
  }
}

module.exports = router;
