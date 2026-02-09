/**
 * 手动运行采集脚本
 * 使用方法: node server/scripts/run-aggregation.js
 */
const { getDatabase, closeDatabase } = require('../database');
const { runAggregation } = require('../services/aggregator');
const { transformPendingArticles } = require('../services/transformer');

async function main() {
  console.log('健康资讯采集脚本启动\n');

  // 初始化数据库
  getDatabase();

  try {
    // 运行采集
    await runAggregation();

    // 转换文章
    transformPendingArticles();

    console.log('\n采集脚本执行完毕');
  } catch (err) {
    console.error('采集脚本执行出错:', err.message);
    process.exitCode = 1;
  } finally {
    closeDatabase();
  }
}

main();
