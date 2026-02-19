const cron = require('node-cron');
const config = require('../config');
const { runAggregation } = require('./aggregator');
const { transformPendingArticles } = require('./transformer');
const { pushDailyDigest, isWechatConfigured } = require('./wechat');

let scheduledTask = null;
let wechatPushTask = null;

/**
 * 启动定时采集任务
 */
function startScheduler() {
  if (scheduledTask) {
    console.log('[调度] 定时任务已在运行中');
    return;
  }

  const cronExpression = config.aggregation.schedule;

  if (!cron.validate(cronExpression)) {
    console.error(`[调度] 无效的 cron 表达式: ${cronExpression}`);
    return;
  }

  scheduledTask = cron.schedule(cronExpression, async () => {
    console.log(`[调度] 定时任务触发 - ${new Date().toLocaleString('zh-CN')}`);

    try {
      // 第一步：采集新文章
      await runAggregation();

      // 第二步：转换待处理文章
      await transformPendingArticles();

      console.log(`[调度] 定时任务完成 - ${new Date().toLocaleString('zh-CN')}`);
    } catch (err) {
      console.error(`[调度] 定时任务执行出错: ${err.message}`);
    }
  });

  console.log(`[调度] 定时采集任务已启动，计划: ${cronExpression}`);
  console.log('[调度] 提示: 默认每天 06:00 和 18:00 自动采集');

  // 微信公众号每日推送（每天 08:00）
  if (isWechatConfigured()) {
    wechatPushTask = cron.schedule('0 8 * * *', async () => {
      console.log(`[调度] 微信公众号推送触发 - ${new Date().toLocaleString('zh-CN')}`);
      try {
        const result = await pushDailyDigest();
        console.log(`[调度] 微信推送结果: ${result.message}`);
      } catch (err) {
        console.error(`[调度] 微信推送出错: ${err.message}`);
      }
    });
    console.log('[调度] 微信公众号每日推送已启动（每天 08:00）');
  }
}

/**
 * 停止定时任务
 */
function stopScheduler() {
  if (scheduledTask) {
    scheduledTask.stop();
    scheduledTask = null;
    console.log('[调度] 定时任务已停止');
  }
  if (wechatPushTask) {
    wechatPushTask.stop();
    wechatPushTask = null;
    console.log('[调度] 微信推送任务已停止');
  }
}

/**
 * 手动触发一次采集和转换
 */
async function triggerManualRun() {
  console.log('[调度] 手动触发采集和转换...');
  try {
    await runAggregation();
    await transformPendingArticles();
    return { success: true, message: '采集和转换完成' };
  } catch (err) {
    console.error(`[调度] 手动触发出错: ${err.message}`);
    return { success: false, message: err.message };
  }
}

module.exports = { startScheduler, stopScheduler, triggerManualRun };
