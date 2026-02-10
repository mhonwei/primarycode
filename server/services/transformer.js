const { getDatabase } = require('../database');
const config = require('../config');
const {
  translateTitle,
  translateContent,
  generateChineseSummary,
  extractKeyPoints,
  assessCredibility,
  HEALTH_DICT,
} = require('./translator');

/**
 * 内容转换服务 v2
 *
 * 将采集到的英文专业健康资讯转换为面向中老年人的
 * 简明中文健康科普内容，并评估信息可信度。
 */

// ===== 分类关键词 =====
const CATEGORY_KEYWORDS = {
  nutrition: [
    'diet', 'nutrition', 'food', 'eat', 'vitamin', 'supplement', 'protein',
    'fiber', 'calorie', 'meal', 'fruit', 'vegetable', 'omega', 'mineral',
    'probiotic', 'Mediterranean', 'whole grain', 'antioxidant',
  ],
  fitness: [
    'exercise', 'fitness', 'workout', 'physical activity', 'aerobic', 'yoga',
    'tai chi', 'walking', 'strength', 'flexibility', 'sports', 'swimming',
    'balance', 'resistance training',
  ],
  disease_prevention: [
    'prevention', 'screening', 'vaccine', 'risk factor', 'early detection',
    'checkup', 'lifestyle', 'immune', 'risk reduction',
  ],
  mental_health: [
    'mental', 'depression', 'anxiety', 'stress', 'sleep', 'insomnia',
    'meditation', 'mindfulness', 'cognitive', 'brain health', 'mood', 'memory',
  ],
  rehabilitation: [
    'rehabilitation', 'recovery', 'therapy', 'physical therapy',
    'occupational therapy', 'post-surgery', 'rehab', 'stroke recovery',
  ],
  elderly_care: [
    'elderly', 'aging', 'senior', 'older adult', 'geriatric', 'alzheimer',
    'dementia', 'osteoporosis', 'fall prevention', 'longevity', 'frailty',
    'sarcopenia', 'cognitive decline', 'healthy aging',
  ],
  chronic_disease: [
    'diabetes', 'hypertension', 'heart disease', 'cardiovascular', 'cholesterol',
    'blood pressure', 'blood sugar', 'chronic', 'obesity', 'metabolic',
  ],
  medical_research: [
    'study', 'research', 'clinical trial', 'finding', 'discovery', 'breakthrough',
    'scientists', 'researchers', 'journal', 'published', 'meta-analysis',
  ],
  public_health: [
    'WHO', 'public health', 'pandemic', 'epidemic', 'outbreak', 'policy',
    'regulation', 'guideline', 'population',
  ],
  traditional_medicine: [
    'traditional', 'herbal', 'chinese medicine', 'acupuncture',
    'natural remedy', 'holistic', 'integrative',
  ],
};

// ===== 受众检测 =====
const AUDIENCE_KEYWORDS = {
  elderly: [
    'senior', 'elderly', 'older', 'aging', 'retirement', 'geriatric',
    'alzheimer', 'dementia', 'osteoporosis', 'arthritis', 'longevity',
    'fall prevention', 'cognitive decline', 'memory loss',
  ],
  middle_aged: [
    'middle-aged', 'midlife', 'prevention', 'screening', 'cholesterol',
    'blood pressure', 'weight management', 'stress', 'work-life',
  ],
};

/**
 * 检测最合适的分类
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
      if (matches) score += matches.length;
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
 * 提取标签
 */
function extractTags(title, content) {
  const text = `${title} ${content}`.toLowerCase();
  const tags = new Set();

  for (const [term, zh] of Object.entries(HEALTH_DICT)) {
    if (text.includes(term.toLowerCase())) {
      const shortTag = zh.replace(/（.*?）/g, '').trim();
      if (shortTag.length >= 2 && shortTag.length <= 6) {
        tags.add(shortTag);
      }
    }
  }

  return Array.from(tags).slice(0, 8);
}

/**
 * 生成面向中老年人的实用健康建议
 */
function generateHealthTips(content, category) {
  const tips = [];

  const categoryTips = {
    nutrition: [
      '每天摄入12种以上食物，保证营养均衡',
      '减少盐分摄入（每天不超过6克），预防高血压',
      '多吃深色蔬菜和粗粮，补充膳食纤维',
      '适量补充优质蛋白质，如鱼类、豆制品、蛋类',
      '控制油脂摄入，优先选择橄榄油、菜籽油等植物油',
    ],
    fitness: [
      '每天步行6000-8000步，维持基本体力',
      '每周至少3次中等强度运动，每次30分钟以上',
      '推荐太极拳、游泳、健步走等低冲击运动',
      '运动前后充分热身和拉伸，预防运动损伤',
      '循序渐进，不要突然剧烈运动',
    ],
    disease_prevention: [
      '每年至少一次全面体检，重点关注三高指标',
      '50岁以上建议每年做一次肠镜筛查',
      '女性40岁以上每年做乳腺和宫颈筛查',
      '定期监测血压、血糖，做好慢病管理',
      '接种流感疫苗和肺炎疫苗，增强免疫力',
    ],
    mental_health: [
      '保持规律作息，每天睡7-8小时',
      '培养兴趣爱好（书法、园艺、下棋等），充实生活',
      '多与家人朋友交流，避免孤独感',
      '学习新技能有助于延缓认知功能下降',
      '如持续感到低落或焦虑，请及时就医',
    ],
    elderly_care: [
      '家中安装防滑垫和扶手，预防跌倒',
      '定期检查视力和听力，及时佩戴辅助器具',
      '保持社交活跃，参加社区活动',
      '每天做简单的脑力练习（阅读、猜谜等）',
      '注意保暖，气温变化时增减衣物',
    ],
    chronic_disease: [
      '遵医嘱按时服药，不要自行停药或调整剂量',
      '定期复查，监测各项指标变化',
      '控制饮食与适度运动是慢病管理的基础',
      '记录每日血压/血糖数据，就诊时提供给医生参考',
    ],
    rehabilitation: [
      '康复训练需在专业指导下进行',
      '循序渐进，急于求成反而不利恢复',
      '保持积极乐观的心态是康复的重要因素',
      '注意营养补充，康复期需要充足的蛋白质',
    ],
    medical_research: [
      '科研成果转化为临床应用通常需要数年时间，请理性看待',
      '不要因为一篇研究就改变用药方案，请咨询主治医生',
      '关注权威医学期刊和机构发布的信息',
    ],
    wellness: [
      '作息规律是养生的根本',
      '保持心情愉悦，情绪健康与身体健康密切相关',
      '春捂秋冻要适度，根据个人体质调整',
    ],
    public_health: [
      '关注国家卫健委等官方渠道发布的健康信息',
      '不信谣不传谣，科学理性看待健康新闻',
    ],
    traditional_medicine: [
      '中医养生因人而异，建议在专业中医师指导下调理',
      '药食同源，日常可适当食用山药、枸杞、红枣等食材',
      '中西医结合往往效果更好，不要排斥任何一方',
    ],
  };

  const relevant = categoryTips[category] || categoryTips.wellness;
  const shuffled = relevant.sort(() => Math.random() - 0.5);
  tips.push(...shuffled.slice(0, 2));

  tips.push('⚕️ 免责声明：本文内容来源于国际科研资讯，仅供健康参考，不能替代医生的专业诊疗意见。如有健康问题，请及时就医。');

  return tips;
}

/**
 * 转换单篇文章（完整流程）
 */
function transformArticle(article) {
  const originalTitle = article.original_title || '';
  const originalContent = article.original_content || '';

  // 1. 翻译
  const title = translateTitle(originalTitle);
  const content = translateContent(originalContent);

  // 2. 生成中文摘要
  const summary = generateChineseSummary(
    originalTitle, originalContent,
    config.transformation.maxSummaryLength
  );

  // 3. 分类与受众
  const category = detectCategory(originalTitle, originalContent);
  const audience = detectAudience(originalTitle, originalContent);

  // 4. 提取标签
  const tags = extractTags(originalTitle, originalContent);

  // 5. 提取关键要点
  const keyPoints = extractKeyPoints(originalTitle, originalContent);

  // 6. 评估可信度
  const credibility = assessCredibility(article.source_name, originalContent);

  // 7. 生成健康建议
  const healthTips = generateHealthTips(originalContent, category);

  // 8. 截断内容到合理长度
  let finalContent = content;
  if (finalContent.length > config.transformation.maxContentLength) {
    finalContent = finalContent.substring(0, config.transformation.maxContentLength);
    const lastPeriod = Math.max(
      finalContent.lastIndexOf('。'),
      finalContent.lastIndexOf('. '),
    );
    if (lastPeriod > finalContent.length * 0.7) {
      finalContent = finalContent.substring(0, lastPeriod + 1);
    }
    finalContent += '\n\n（更多详情请查看原文链接）';
  }

  // 9. 在内容前添加要点和可信度
  let enrichedContent = '';

  if (credibility) {
    enrichedContent += `📊 信息可信度：${credibility.label}`;
    if (credibility.factors.length > 0) {
      enrichedContent += `（${credibility.factors.join('、')}）`;
    }
    enrichedContent += '\n\n';
  }

  if (keyPoints.length > 0) {
    enrichedContent += '📌 核心要点：\n';
    keyPoints.forEach((point, i) => {
      enrichedContent += `${i + 1}. ${point}\n`;
    });
    enrichedContent += '\n';
  }

  enrichedContent += finalContent;

  return {
    title,
    summary,
    content: enrichedContent,
    category,
    audience: JSON.stringify(audience),
    tags: JSON.stringify(tags),
    health_tips: JSON.stringify(healthTips),
    key_points: JSON.stringify(keyPoints),
    credibility_score: credibility ? credibility.score : 0,
    credibility_level: credibility ? credibility.level : 'medium',
    credibility_factors: credibility ? JSON.stringify(credibility.factors) : '[]',
  };
}

/**
 * 批量转换待处理文章
 */
function transformPendingArticles(limit = 50) {
  const db = getDatabase();
  const pending = db
    .prepare("SELECT * FROM articles WHERE status = 'pending' ORDER BY aggregated_at DESC LIMIT ?")
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
      key_points = @key_points,
      credibility_score = @credibility_score,
      credibility_level = @credibility_level,
      credibility_factors = @credibility_factors,
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
  translateTitle,
  translateContent: translateContent,
  generateChineseSummary,
  detectCategory,
  detectAudience,
  extractTags,
  extractHealthTips: generateHealthTips,
};
