const path = require('path');

module.exports = {
  // 服务器配置
  port: process.env.PORT || 3000,
  host: process.env.HOST || '0.0.0.0',

  // 数据库配置
  dbPath: process.env.DB_PATH || path.join(__dirname, '..', 'data', 'health_news.db'),

  // 新闻采集配置
  aggregation: {
    // 采集间隔（cron 表达式）: 默认每天早上 6:00 和下午 18:00 各采集一次
    schedule: process.env.CRON_SCHEDULE || '0 6,18 * * *',

    // ===== 数据源列表 =====
    // type: 'rss' = RSS订阅, 'web' = 网页抓取
    sources: [
      // --- 国内健康资讯源（国内网络可直接访问） ---
      {
        name: '人民网健康',
        url: 'http://health.people.com.cn/rss/health.xml',
        type: 'rss',
        category: 'public_health',
        language: 'zh',
      },
      {
        name: '丁香医生',
        url: 'https://dxy.com',
        type: 'web',
        category: 'wellness',
        language: 'zh',
        scrapeConfig: {
          listUrl: 'https://www.dxy.cn/column/health',
          articleSelector: '.health-article-item, .article-item, article a',
          titleSelector: 'h2, h3, .title',
          linkAttr: 'href',
          baseUrl: 'https://www.dxy.cn',
        },
      },
      {
        name: '健康时报',
        url: 'https://www.jksb.com.cn',
        type: 'web',
        category: 'wellness',
        language: 'zh',
        scrapeConfig: {
          listUrl: 'https://www.jksb.com.cn/html/diseases/',
          articleSelector: '.list-item a, .article-list a, .news-list li a',
          titleSelector: '',
          linkAttr: 'href',
          baseUrl: 'https://www.jksb.com.cn',
        },
      },
      {
        name: '中国疾控中心',
        url: 'https://www.chinacdc.cn',
        type: 'web',
        category: 'disease_prevention',
        language: 'zh',
        scrapeConfig: {
          listUrl: 'https://www.chinacdc.cn/jkzt/',
          articleSelector: '.list_item a, .listBox a, .conBox li a',
          titleSelector: '',
          linkAttr: 'href',
          baseUrl: 'https://www.chinacdc.cn',
        },
      },

      // --- 国际权威健康源（需国际网络） ---
      {
        name: 'Medical News Today',
        url: 'https://www.medicalnewstoday.com/rss',
        type: 'rss',
        category: 'medical_research',
        language: 'en',
      },
      {
        name: 'WHO News',
        url: 'https://www.who.int/rss-feeds/news-english.xml',
        type: 'rss',
        category: 'public_health',
        language: 'en',
      },
      {
        name: 'Harvard Health Blog',
        url: 'https://www.health.harvard.edu/blog/feed',
        type: 'rss',
        category: 'wellness',
        language: 'en',
      },
      {
        name: 'ScienceDaily Health',
        url: 'https://www.sciencedaily.com/rss/health_medicine.xml',
        type: 'rss',
        category: 'medical_research',
        language: 'en',
      },
      {
        name: 'NIH Research Matters',
        url: 'https://www.nih.gov/news-events/nih-research-matters/feed',
        type: 'rss',
        category: 'medical_research',
        language: 'en',
      },
      {
        name: 'Nature Medicine',
        url: 'https://www.nature.com/nm.rss',
        type: 'rss',
        category: 'medical_research',
        language: 'en',
      },
      {
        name: 'PubMed Trending',
        url: 'https://pubmed.ncbi.nlm.nih.gov/trending/',
        type: 'web',
        category: 'medical_research',
        language: 'en',
        scrapeConfig: {
          listUrl: 'https://pubmed.ncbi.nlm.nih.gov/trending/',
          articleSelector: '.docsum-content',
          titleSelector: '.docsum-title',
          linkSelector: 'a',
          linkAttr: 'href',
          baseUrl: 'https://pubmed.ncbi.nlm.nih.gov',
          summarySelector: '.full-view-snippet',
        },
      },
      {
        name: 'WebMD Health',
        url: 'https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC',
        type: 'rss',
        category: 'wellness',
        language: 'en',
      },
    ],

    // 保留旧字段兼容（指向sources中type=rss的项）
    get rssSources() {
      return this.sources.filter(s => s.type === 'rss');
    },

    // 网页抓取源
    get webSources() {
      return this.sources.filter(s => s.type === 'web');
    },

    // 每个源最多获取的文章数
    maxArticlesPerSource: 20,

    // 文章保留天数
    retentionDays: 90,

    // 请求超时（毫秒）
    requestTimeout: 15000,

    // 请求间隔（毫秒），避免被封
    requestDelay: 2000,
  },

  // 内容分类（面向中老年人优化排序）
  categories: [
    { id: 'chronic_disease', name: '慢病管理', icon: '💊', description: '三高、糖尿病等慢性病管理' },
    { id: 'nutrition', name: '饮食营养', icon: '🥗', description: '科学饮食与营养指导' },
    { id: 'elderly_care', name: '乐龄健康', icon: '🌿', description: '中老年人健康管理与抗衰' },
    { id: 'fitness', name: '运动康健', icon: '🚶', description: '适合中老年的科学运动' },
    { id: 'disease_prevention', name: '疾病预防', icon: '🛡️', description: '筛查、疫苗与风险防控' },
    { id: 'mental_health', name: '身心调养', icon: '🧘', description: '睡眠、情绪与认知健康' },
    { id: 'medical_research', name: '前沿发现', icon: '🔬', description: '国际医学最新科研成果' },
    { id: 'rehabilitation', name: '康复护理', icon: '🏥', description: '术后康复与护理指导' },
    { id: 'wellness', name: '养生之道', icon: '☯️', description: '四季养生与生活智慧' },
    { id: 'traditional_medicine', name: '中医养生', icon: '🍵', description: '传统中医与药食同源' },
    { id: 'public_health', name: '健康资讯', icon: '📋', description: '公共卫生与健康政策' },
  ],

  // 内容转换配置
  transformation: {
    // 目标阅读水平：适合中老年人的简明语言
    readingLevel: 'accessible',
    // 最大摘要长度（字符数）
    maxSummaryLength: 500,
    // 最大正文长度（字符数）
    maxContentLength: 3000,
  },
};
