const express = require('express');
const { getAggregationStats } = require('../services/aggregator');
const { transformPendingArticles } = require('../services/transformer');
const { triggerManualRun } = require('../services/scheduler');

const router = express.Router();

/**
 * GET /api/admin/stats
 * 获取系统统计信息
 */
router.get('/stats', (req, res) => {
  const stats = getAggregationStats();
  res.json({ success: true, data: stats });
});

/**
 * POST /api/admin/aggregate
 * 手动触发采集
 */
router.post('/aggregate', async (req, res) => {
  try {
    const result = await triggerManualRun();
    res.json({ success: result.success, message: result.message });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

/**
 * POST /api/admin/transform
 * 手动触发内容转换
 */
router.post('/transform', (req, res) => {
  try {
    const result = transformPendingArticles();
    res.json({ success: true, data: result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

module.exports = router;
