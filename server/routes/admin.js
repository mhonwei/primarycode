const express = require('express');
const { getAggregationStats } = require('../services/aggregator');
const { transformPendingArticles } = require('../services/transformer');
const { triggerManualRun } = require('../services/scheduler');
const { pushDailyDigest, isWechatConfigured } = require('../services/wechat');

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
router.post('/transform', async (req, res) => {
  try {
    const result = await transformPendingArticles();
    res.json({ success: true, data: result });
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

/**
 * POST /api/admin/wechat-push
 * 手动触发微信公众号推送
 */
router.post('/wechat-push', async (req, res) => {
  try {
    if (!isWechatConfigured()) {
      return res.status(400).json({
        success: false,
        message: '未配置微信公众号，请设置 WECHAT_APPID 和 WECHAT_SECRET 环境变量',
      });
    }
    const count = req.body.count || 5;
    const result = await pushDailyDigest(count);
    res.json(result);
  } catch (err) {
    res.status(500).json({ success: false, message: err.message });
  }
});

module.exports = router;
