const cheerio = require('cheerio');
const config = require('../config');

/**
 * 网页抓取服务
 *
 * 用于从没有RSS的网站抓取健康资讯，包括：
 * - 国内健康网站（丁香医生、健康时报、中国疾控中心等）
 * - 国际医学网站（PubMed等）
 */

/**
 * 抓取网页内容
 */
async function fetchPage(url, timeout) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout || config.aggregation.requestTimeout);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'identity',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    // 处理不同编码
    const buffer = await response.arrayBuffer();
    let html = new TextDecoder('utf-8').decode(buffer);

    // 如果检测到是GBK编码，重新解码
    if (html.includes('charset=gb2312') || html.includes('charset=gbk') || html.includes('charset=GB2312')) {
      try {
        html = new TextDecoder('gbk').decode(buffer);
      } catch {
        // fallback to utf-8
      }
    }

    return html;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * 抓取文章详情页面内容
 */
async function fetchArticleContent(url) {
  try {
    const html = await fetchPage(url);
    const $ = cheerio.load(html);

    // 移除脚本、样式、导航等无关元素
    $('script, style, nav, header, footer, .sidebar, .ad, .comment, .share, iframe, .navigation').remove();

    // 尝试常见的正文容器
    const contentSelectors = [
      '.article-content', '.post-content', '.entry-content',
      '.content-text', '.article-body', '.news-content',
      '.TRS_Editor', '.con_text', '.article_content',
      '#content', '#articleContent', '.detail-content',
      'article', '.main-content', '.text',
    ];

    let content = '';
    for (const sel of contentSelectors) {
      const el = $(sel);
      if (el.length && el.text().trim().length > 100) {
        content = el.text().trim();
        break;
      }
    }

    // 如果没找到，取body中最长的文本块
    if (!content) {
      $('p').each(function () {
        const text = $(this).text().trim();
        if (text.length > 50) {
          content += text + '\n';
        }
      });
    }

    // 清理多余空白
    content = content
      .replace(/\s+/g, ' ')
      .replace(/\n\s+/g, '\n')
      .trim();

    return content.substring(0, 5000);
  } catch (err) {
    console.error(`[抓取] 文章内容获取失败 ${url}: ${err.message}`);
    return '';
  }
}

/**
 * 从网页源抓取文章列表
 */
async function scrapeSource(source) {
  const results = { found: 0, added: 0, articles: [], errors: [] };
  const sc = source.scrapeConfig;

  if (!sc || !sc.listUrl) {
    results.errors.push('缺少抓取配置');
    return results;
  }

  try {
    console.log(`[抓取] 正在从 ${source.name} 获取内容...`);
    const html = await fetchPage(sc.listUrl);
    const $ = cheerio.load(html);

    const articles = [];
    const baseUrl = sc.baseUrl || '';

    // 解析文章列表
    $(sc.articleSelector).each(function (i) {
      if (i >= config.aggregation.maxArticlesPerSource) return false;

      const el = $(this);

      // 提取标题
      let title = '';
      if (sc.titleSelector) {
        title = el.find(sc.titleSelector).first().text().trim();
      }
      if (!title) {
        title = el.text().trim();
      }

      // 提取链接
      let link = '';
      if (sc.linkSelector) {
        link = el.find(sc.linkSelector).first().attr(sc.linkAttr || 'href') || '';
      } else {
        link = el.attr(sc.linkAttr || 'href') || el.find('a').first().attr('href') || '';
      }

      // 处理相对路径
      if (link && !link.startsWith('http')) {
        if (link.startsWith('//')) {
          link = 'https:' + link;
        } else if (link.startsWith('/')) {
          link = baseUrl + link;
        } else {
          link = baseUrl + '/' + link;
        }
      }

      // 清理标题
      title = title.replace(/\s+/g, ' ').substring(0, 200);

      if (title && title.length > 5 && link) {
        articles.push({ title, link });
      }
    });

    results.found = articles.length;
    console.log(`[抓取] ${source.name}: 找到 ${articles.length} 篇文章`);

    // 逐篇获取详情
    for (const article of articles) {
      try {
        // 间隔请求，避免被封
        if (config.aggregation.requestDelay > 0) {
          await sleep(config.aggregation.requestDelay);
        }

        let content = '';
        // 只对有意义的链接获取详情
        if (article.link && !article.link.includes('javascript:')) {
          content = await fetchArticleContent(article.link);
        }

        results.articles.push({
          source_name: source.name,
          source_url: source.url,
          original_title: article.title,
          original_content: content || article.title,
          original_link: article.link,
          original_language: source.language || 'zh',
          category: source.category || 'wellness',
          published_at: new Date().toISOString(),
        });
        results.added++;
      } catch (err) {
        results.errors.push(`文章 "${article.title}": ${err.message}`);
      }
    }

    console.log(`[抓取] ${source.name}: 成功获取 ${results.added} 篇文章内容`);
  } catch (err) {
    const errorMsg = `${source.name} 抓取失败: ${err.message}`;
    console.error(`[抓取] ${errorMsg}`);
    results.errors.push(errorMsg);
  }

  return results;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
  scrapeSource,
  fetchPage,
  fetchArticleContent,
};
