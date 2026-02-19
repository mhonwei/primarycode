const express = require('express');
const { getDatabase } = require('../database');
const config = require('../config');

const router = express.Router();

/**
 * GET /api/categories
 * 获取所有分类及其文章数量
 */
router.get('/', (req, res) => {
  const db = getDatabase();

  const categoryCounts = db
    .prepare(
      `SELECT category, COUNT(*) as count
       FROM articles
       WHERE status = 'transformed'
       GROUP BY category`
    )
    .all();

  const countMap = {};
  for (const row of categoryCounts) {
    countMap[row.category] = row.count;
  }

  const categories = config.categories.map((cat) => ({
    ...cat,
    articleCount: countMap[cat.id] || 0,
  }));

  res.json({
    success: true,
    data: categories,
  });
});

/**
 * GET /api/categories/:id
 * 获取单个分类信息
 */
router.get('/:id', (req, res) => {
  const { id } = req.params;
  const category = config.categories.find((c) => c.id === id);

  if (!category) {
    return res.status(404).json({ success: false, message: '分类不存在' });
  }

  const db = getDatabase();
  const count = db
    .prepare(
      "SELECT COUNT(*) as count FROM articles WHERE status = 'transformed' AND category = ?"
    )
    .get(id);

  res.json({
    success: true,
    data: {
      ...category,
      articleCount: count.count,
    },
  });
});

module.exports = router;
