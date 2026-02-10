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

    // RSS 源列表 - 健康/科学/养生类
    rssSources: [
      {
        name: 'Medical News Today',
        url: 'https://www.medicalnewstoday.com/rss',
        category: 'medical_research',
        language: 'en',
      },
      {
        name: 'WHO News',
        url: 'https://www.who.int/rss-feeds/news-english.xml',
        category: 'public_health',
        language: 'en',
      },
      {
        name: 'Harvard Health Blog',
        url: 'https://www.health.harvard.edu/blog/feed',
        category: 'wellness',
        language: 'en',
      },
      {
        name: 'ScienceDaily Health',
        url: 'https://www.sciencedaily.com/rss/health_medicine.xml',
        category: 'medical_research',
        language: 'en',
      },
      {
        name: 'NIH Research Matters',
        url: 'https://www.nih.gov/news-events/nih-research-matters/feed',
        category: 'medical_research',
        language: 'en',
      },
      {
        name: 'Nature Medicine',
        url: 'https://www.nature.com/nm.rss',
        category: 'medical_research',
        language: 'en',
      },
      {
        name: 'WebMD Health',
        url: 'https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC',
        category: 'wellness',
        language: 'en',
      },
    ],

    // 每个源最多获取的文章数
    maxArticlesPerSource: 20,

    // 文章保留天数
    retentionDays: 90,
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
