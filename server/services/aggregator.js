const RSSParser = require('rss-parser');
const config = require('../config');
const { getDatabase } = require('../database');

const rssParser = new RSSParser({
  timeout: 15000,
  headers: {
    'User-Agent': 'HealthNewsAggregator/1.0',
    Accept: 'application/rss+xml, application/xml, text/xml',
  },
});

/**
 * 从单个 RSS 源采集文章
 */
async function fetchFromSource(source) {
  const results = { found: 0, added: 0, errors: [] };

  try {
    console.log(`[采集] 正在从 ${source.name} 获取内容...`);
    const feed = await rssParser.parseURL(source.url);
    const items = feed.items.slice(0, config.aggregation.maxArticlesPerSource);
    results.found = items.length;

    const db = getDatabase();
    const insertStmt = db.prepare(`
      INSERT OR IGNORE INTO articles
        (source_name, source_url, original_title, original_content, original_link,
         original_language, category, published_at, status)
      VALUES
        (@source_name, @source_url, @original_title, @original_content, @original_link,
         @original_language, @category, @published_at, 'pending')
    `);

    for (const item of items) {
      try {
        const result = insertStmt.run({
          source_name: source.name,
          source_url: source.url,
          original_title: item.title || '无标题',
          original_content: item.contentSnippet || item.content || item.summary || '',
          original_link: item.link || item.guid || `${source.url}#${Date.now()}`,
          original_language: source.language || 'en',
          category: source.category || 'wellness',
          published_at: item.pubDate || item.isoDate || new Date().toISOString(),
        });
        if (result.changes > 0) {
          results.added++;
        }
      } catch (err) {
        results.errors.push(`文章 "${item.title}": ${err.message}`);
      }
    }

    console.log(`[采集] ${source.name}: 发现 ${results.found} 篇, 新增 ${results.added} 篇`);
  } catch (err) {
    const errorMsg = `源 ${source.name} 采集失败: ${err.message}`;
    console.error(`[采集] ${errorMsg}`);
    results.errors.push(errorMsg);
  }

  return results;
}

/**
 * 运行完整的采集流程
 */
async function runAggregation() {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`[采集] 开始采集任务 - ${new Date().toLocaleString('zh-CN')}`);
  console.log(`${'='.repeat(60)}`);

  const db = getDatabase();
  const sources = config.aggregation.rssSources;
  const totalResults = { sourcesProcessed: 0, totalFound: 0, totalAdded: 0, errors: [] };

  for (const source of sources) {
    const logEntry = db
      .prepare('INSERT INTO aggregation_logs (source_name) VALUES (?)')
      .run(source.name);
    const logId = logEntry.lastInsertRowid;

    const results = await fetchFromSource(source);

    totalResults.sourcesProcessed++;
    totalResults.totalFound += results.found;
    totalResults.totalAdded += results.added;
    totalResults.errors.push(...results.errors);

    db.prepare(
      `UPDATE aggregation_logs
       SET articles_found = ?, articles_added = ?, errors = ?, finished_at = CURRENT_TIMESTAMP
       WHERE id = ?`
    ).run(results.found, results.added, JSON.stringify(results.errors), logId);
  }

  // 清理过期文章
  cleanOldArticles();

  console.log(`\n[采集] 采集完成汇总:`);
  console.log(`  - 处理源: ${totalResults.sourcesProcessed}/${sources.length}`);
  console.log(`  - 发现文章: ${totalResults.totalFound}`);
  console.log(`  - 新增文章: ${totalResults.totalAdded}`);
  if (totalResults.errors.length > 0) {
    console.log(`  - 错误数: ${totalResults.errors.length}`);
  }
  console.log(`${'='.repeat(60)}\n`);

  return totalResults;
}

/**
 * 清理过期文章
 */
function cleanOldArticles() {
  const db = getDatabase();
  const retentionDays = config.aggregation.retentionDays;

  const result = db
    .prepare(
      `DELETE FROM articles
     WHERE aggregated_at < datetime('now', '-' || ? || ' days')
     AND like_count = 0 AND share_count = 0`
    )
    .run(retentionDays);

  if (result.changes > 0) {
    console.log(`[清理] 已清理 ${result.changes} 篇过期文章`);
  }
}

/**
 * 获取待处理的文章列表
 */
function getPendingArticles(limit = 50) {
  const db = getDatabase();
  return db
    .prepare(
      `SELECT * FROM articles
     WHERE status = 'pending'
     ORDER BY aggregated_at DESC
     LIMIT ?`
    )
    .all(limit);
}

/**
 * 获取采集统计
 */
function getAggregationStats() {
  const db = getDatabase();

  const total = db.prepare('SELECT COUNT(*) as count FROM articles').get();
  const pending = db
    .prepare("SELECT COUNT(*) as count FROM articles WHERE status = 'pending'")
    .get();
  const transformed = db
    .prepare("SELECT COUNT(*) as count FROM articles WHERE status = 'transformed'")
    .get();
  const lastLog = db
    .prepare('SELECT * FROM aggregation_logs ORDER BY started_at DESC LIMIT 1')
    .get();

  return {
    totalArticles: total.count,
    pendingArticles: pending.count,
    transformedArticles: transformed.count,
    lastAggregation: lastLog,
  };
}

module.exports = {
  runAggregation,
  fetchFromSource,
  getPendingArticles,
  getAggregationStats,
  cleanOldArticles,
};
