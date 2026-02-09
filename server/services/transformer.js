const { getDatabase } = require('../database');
const config = require('../config');

/**
 * 内容转换服务
 *
 * 将采集到的英文/专业健康资讯转换为面向中老年人的
 * 简明中文健康科普内容。
 *
 * 当前实现使用基于规则的本地转换。
 * 可扩展为调用 AI API（如 OpenAI、Claude、百度文心等）进行智能翻译和改写。
 */

// 常用健康领域英中术语映射
const HEALTH_TERMS = {
  // 疾病与症状
  diabetes: '糖尿病',
  hypertension: '高血压',
  'high blood pressure': '高血压',
  cholesterol: '胆固醇',
  obesity: '肥胖症',
  cancer: '癌症',
  'heart disease': '心脏病',
  cardiovascular: '心血管',
  stroke: '中风',
  alzheimer: '阿尔茨海默病（老年痴呆）',
  dementia: '痴呆症',
  arthritis: '关节炎',
  osteoporosis: '骨质疏松',
  insomnia: '失眠',
  depression: '抑郁症',
  anxiety: '焦虑症',
  inflammation: '炎症',
  infection: '感染',
  allergy: '过敏',
  asthma: '哮喘',
  pneumonia: '肺炎',

  // 营养与饮食
  protein: '蛋白质',
  vitamin: '维生素',
  mineral: '矿物质',
  fiber: '膳食纤维',
  antioxidant: '抗氧化剂',
  omega: 'Omega脂肪酸',
  calcium: '钙',
  iron: '铁',
  zinc: '锌',
  probiotic: '益生菌',
  supplement: '营养补充剂',
  calorie: '卡路里（热量）',
  carbohydrate: '碳水化合物',
  metabolism: '新陈代谢',

  // 医学术语
  clinical: '临床',
  trial: '试验',
  'clinical trial': '临床试验',
  study: '研究',
  research: '研究',
  therapy: '疗法',
  treatment: '治疗',
  diagnosis: '诊断',
  symptom: '症状',
  vaccine: '疫苗',
  antibody: '抗体',
  immune: '免疫',
  'immune system': '免疫系统',
  gene: '基因',
  dna: 'DNA（脱氧核糖核酸）',

  // 运动与健身
  exercise: '运动',
  fitness: '健身',
  aerobic: '有氧运动',
  stretching: '拉伸运动',
  yoga: '瑜伽',
  walking: '步行',
  'tai chi': '太极拳',
  meditation: '冥想',
  'blood pressure': '血压',
  'heart rate': '心率',
  bmi: 'BMI（身体质量指数）',
};

// 分类关键词映射
const CATEGORY_KEYWORDS = {
  nutrition: [
    'diet',
    'nutrition',
    'food',
    'eat',
    'vitamin',
    'supplement',
    'protein',
    'fiber',
    'calorie',
    'meal',
    'fruit',
    'vegetable',
    'omega',
    'mineral',
    'probiotic',
  ],
  fitness: [
    'exercise',
    'fitness',
    'workout',
    'physical activity',
    'aerobic',
    'yoga',
    'tai chi',
    'walking',
    'strength',
    'flexibility',
    'sports',
  ],
  disease_prevention: [
    'prevention',
    'screening',
    'vaccine',
    'risk factor',
    'early detection',
    'checkup',
    'lifestyle',
    'immune',
  ],
  mental_health: [
    'mental',
    'depression',
    'anxiety',
    'stress',
    'sleep',
    'insomnia',
    'meditation',
    'mindfulness',
    'cognitive',
    'brain health',
    'mood',
  ],
  rehabilitation: [
    'rehabilitation',
    'recovery',
    'therapy',
    'physical therapy',
    'occupational therapy',
    'post-surgery',
    'rehab',
  ],
  elderly_care: [
    'elderly',
    'aging',
    'senior',
    'older adult',
    'geriatric',
    'alzheimer',
    'dementia',
    'osteoporosis',
    'fall prevention',
  ],
  medical_research: [
    'study',
    'research',
    'clinical trial',
    'finding',
    'discovery',
    'breakthrough',
    'scientists',
    'researchers',
    'journal',
    'published',
  ],
  public_health: [
    'WHO',
    'public health',
    'pandemic',
    'epidemic',
    'outbreak',
    'policy',
    'regulation',
    'guideline',
    'population',
  ],
  traditional_medicine: [
    'traditional',
    'herbal',
    'chinese medicine',
    'acupuncture',
    'natural remedy',
    'holistic',
    'integrative',
  ],
};

// 受众关键词映射
const AUDIENCE_KEYWORDS = {
  elderly: [
    'senior',
    'elderly',
    'older',
    'aging',
    'retirement',
    'geriatric',
    'alzheimer',
    'dementia',
    'osteoporosis',
    'arthritis',
  ],
  youth: [
    'young',
    'student',
    'teenager',
    'adolescent',
    'college',
    'millennial',
    'fitness',
    'sports',
    'mental health',
    'anxiety',
  ],
  all: [],
};

/**
 * 自动检测文章最合适的分类
 */
function detectCategory(title, content) {
  const text = `${title} ${content}`.toLowerCase();
  let bestCategory = 'wellness';
  let bestScore = 0;

  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    let score = 0;
    for (const keyword of keywords) {
      const regex = new RegExp(keyword, 'gi');
      const matches = text.match(regex);
      if (matches) {
        score += matches.length;
      }
    }
    if (score > bestScore) {
      bestScore = score;
      bestCategory = category;
    }
  }

  return bestCategory;
}

/**
 * 检测目标受众
 */
function detectAudience(title, content) {
  const text = `${title} ${content}`.toLowerCase();
  const audiences = [];

  for (const [audience, keywords] of Object.entries(AUDIENCE_KEYWORDS)) {
    if (audience === 'all') continue;
    for (const keyword of keywords) {
      if (text.includes(keyword)) {
        audiences.push(audience);
        break;
      }
    }
  }

  return audiences.length > 0 ? audiences : ['all'];
}

/**
 * 简单的标题翻译/转换
 * 基于规则的转换，实际项目建议接入翻译 API
 */
function transformTitle(originalTitle) {
  let title = originalTitle;

  // 替换已知术语
  for (const [en, zh] of Object.entries(HEALTH_TERMS)) {
    const regex = new RegExp(`\\b${en}\\b`, 'gi');
    title = title.replace(regex, zh);
  }

  // 如果标题仍然主要是英文，添加前缀说明
  const chineseCharCount = (title.match(/[\u4e00-\u9fff]/g) || []).length;
  const totalLength = title.length;

  if (chineseCharCount / totalLength < 0.3 && totalLength > 10) {
    // 标题主要是英文，保留已替换术语的版本并添加标注
    return `【健康资讯】${title}`;
  }

  return title;
}

/**
 * 转换文章内容，使其适合目标读者
 */
function transformContent(originalContent, category) {
  if (!originalContent) return '';

  let content = originalContent;

  // 替换健康术语
  for (const [en, zh] of Object.entries(HEALTH_TERMS)) {
    const regex = new RegExp(`\\b${en}\\b`, 'gi');
    content = content.replace(regex, zh);
  }

  // 截断到合理长度
  if (content.length > config.transformation.maxContentLength) {
    content = content.substring(0, config.transformation.maxContentLength);
    // 在最后一个完整句子处截断
    const lastPeriod = Math.max(
      content.lastIndexOf('。'),
      content.lastIndexOf('. '),
      content.lastIndexOf('！'),
      content.lastIndexOf('？')
    );
    if (lastPeriod > content.length * 0.7) {
      content = content.substring(0, lastPeriod + 1);
    }
    content += '\n\n（更多详情请查看原文链接）';
  }

  return content;
}

/**
 * 生成摘要
 */
function generateSummary(content) {
  if (!content) return '';

  // 提取前几句作为摘要
  const sentences = content.split(/[.。！？!?]+/).filter((s) => s.trim().length > 10);
  let summary = '';

  for (const sentence of sentences) {
    if (summary.length + sentence.length > config.transformation.maxSummaryLength) {
      break;
    }
    summary += sentence.trim() + '。';
  }

  return summary || content.substring(0, config.transformation.maxSummaryLength) + '...';
}

/**
 * 从内容中提取健康建议/实用提示
 */
function extractHealthTips(content, category) {
  const tips = [];
  const text = (content || '').toLowerCase();

  // 基于分类生成通用健康提示
  const categoryTips = {
    nutrition: [
      '均衡饮食是健康的基础，建议每天摄入多种颜色的蔬果',
      '控制盐分和糖分摄入，有助于预防慢性疾病',
      '适量饮水，成年人每天建议饮水1500-1700毫升',
    ],
    fitness: [
      '每周至少进行150分钟中等强度有氧运动',
      '运动前做好热身，运动后注意拉伸放松',
      '中老年人适合太极拳、散步、游泳等低冲击运动',
    ],
    disease_prevention: [
      '定期体检是早期发现疾病的重要手段',
      '保持良好的生活习惯是预防疾病的最佳方式',
      '注意个人卫生，养成勤洗手的好习惯',
    ],
    mental_health: [
      '保证充足的睡眠，成年人每天建议睡7-8小时',
      '适当社交活动有助于维护心理健康',
      '感到持续焦虑或抑郁时，建议寻求专业帮助',
    ],
    rehabilitation: [
      '康复训练需要在专业指导下进行',
      '循序渐进，不要操之过急',
      '保持积极乐观的心态有助于康复',
    ],
    elderly_care: [
      '中老年人应定期检查血压、血糖和血脂',
      '注意防跌倒，保持家中环境安全整洁',
      '适度进行脑力活动，如阅读、下棋等，有助于延缓认知衰退',
    ],
    medical_research: ['科研成果从实验室到临床应用需要时间，请理性看待', '有健康问题请咨询专业医生，勿自行用药'],
    wellness: ['养成规律作息的好习惯', '保持心情愉悦，适当参加社交活动', '中医养生讲究"治未病"，重在预防'],
    public_health: ['关注官方卫生部门发布的健康信息', '理性看待健康新闻，不信谣不传谣'],
    traditional_medicine: [
      '中医养生讲究因人而异，建议在专业中医师指导下调理',
      '药食同源，日常饮食中可适当加入养生食材',
    ],
  };

  const relevantTips = categoryTips[category] || categoryTips.wellness;

  // 随机选取1-2条提示
  const shuffled = relevantTips.sort(() => Math.random() - 0.5);
  tips.push(...shuffled.slice(0, 2));

  // 添加免责声明
  tips.push('温馨提示：本文内容仅供参考，不构成医疗建议。如有健康问题，请咨询专业医生。');

  return tips;
}

/**
 * 提取标签
 */
function extractTags(title, content) {
  const text = `${title} ${content}`.toLowerCase();
  const tags = new Set();

  for (const [term, zh] of Object.entries(HEALTH_TERMS)) {
    if (text.includes(term.toLowerCase())) {
      // 使用简短的中文标签
      const shortTag = zh.replace(/（.*?）/g, '').trim();
      if (shortTag.length <= 6) {
        tags.add(shortTag);
      }
    }
  }

  // 限制标签数量
  return Array.from(tags).slice(0, 8);
}

/**
 * 转换单篇文章
 */
function transformArticle(article) {
  const title = transformTitle(article.original_title);
  const content = transformContent(article.original_content, article.category);
  const summary = generateSummary(content);
  const category = detectCategory(article.original_title, article.original_content);
  const audience = detectAudience(article.original_title, article.original_content);
  const tags = extractTags(article.original_title, article.original_content);
  const healthTips = extractHealthTips(article.original_content, category);

  return {
    title,
    summary,
    content,
    category,
    audience: JSON.stringify(audience),
    tags: JSON.stringify(tags),
    health_tips: JSON.stringify(healthTips),
  };
}

/**
 * 批量转换待处理的文章
 */
function transformPendingArticles(limit = 50) {
  const db = getDatabase();
  const pending = db
    .prepare(
      `SELECT * FROM articles WHERE status = 'pending' ORDER BY aggregated_at DESC LIMIT ?`
    )
    .all(limit);

  console.log(`[转换] 开始处理 ${pending.length} 篇待转换文章...`);

  const updateStmt = db.prepare(`
    UPDATE articles SET
      title = @title,
      summary = @summary,
      content = @content,
      category = @category,
      audience = @audience,
      tags = @tags,
      health_tips = @health_tips,
      status = 'transformed',
      transformed_at = CURRENT_TIMESTAMP
    WHERE id = @id
  `);

  let transformed = 0;
  let errors = 0;

  for (const article of pending) {
    try {
      const result = transformArticle(article);
      updateStmt.run({ ...result, id: article.id });
      transformed++;
    } catch (err) {
      console.error(`[转换] 文章 #${article.id} 转换失败: ${err.message}`);
      errors++;
    }
  }

  console.log(`[转换] 完成: 成功 ${transformed} 篇, 失败 ${errors} 篇`);
  return { transformed, errors };
}

module.exports = {
  transformArticle,
  transformPendingArticles,
  transformTitle,
  transformContent,
  generateSummary,
  detectCategory,
  detectAudience,
  extractTags,
  extractHealthTips,
};
