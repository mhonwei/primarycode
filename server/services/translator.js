/**
 * 英文→中文翻译服务
 *
 * 翻译策略（按优先级）：
 * 1. 百度翻译API（免费标准版，每秒1次，每月5万字符免费）
 * 2. 内置词典翻译（离线兜底）
 *
 * 配置方式（在 .env 或环境变量中设置）：
 *   BAIDU_TRANSLATE_APPID=你的appid
 *   BAIDU_TRANSLATE_SECRET=你的密钥
 *
 * 申请地址：https://fanyi-api.baidu.com/
 * 选「通用文本翻译」→「标准版」（免费）
 */

const crypto = require('crypto');
const config = require('../config');

// ===== 百度翻译 API 配置 =====
const BAIDU_API_URL = 'https://fanyi-api.baidu.com/api/trans/vip/translate';
const BAIDU_APPID = process.env.BAIDU_TRANSLATE_APPID || '';
const BAIDU_SECRET = process.env.BAIDU_TRANSLATE_SECRET || '';

// 限流：标准版每秒1次请求
let lastApiCall = 0;
const API_INTERVAL = 1100; // 毫秒

/**
 * 检查是否配置了百度翻译API
 */
function isBaiduConfigured() {
  return BAIDU_APPID && BAIDU_SECRET;
}

/**
 * 调用百度翻译API
 */
async function baiduTranslate(text, from = 'auto', to = 'zh') {
  if (!isBaiduConfigured()) return null;
  if (!text || text.trim().length === 0) return '';

  // 限流等待
  const now = Date.now();
  const waitTime = API_INTERVAL - (now - lastApiCall);
  if (waitTime > 0) {
    await new Promise(r => setTimeout(r, waitTime));
  }
  lastApiCall = Date.now();

  const salt = Date.now().toString();
  const sign = crypto
    .createHash('md5')
    .update(BAIDU_APPID + text + salt + BAIDU_SECRET)
    .digest('hex');

  const params = new URLSearchParams({
    q: text,
    from,
    to,
    appid: BAIDU_APPID,
    salt,
    sign,
  });

  try {
    const response = await fetch(`${BAIDU_API_URL}?${params}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const data = await response.json();

    if (data.error_code) {
      console.error(`[翻译API] 百度翻译错误: ${data.error_code} - ${data.error_msg}`);
      return null; // 回退到词典翻译
    }

    if (data.trans_result && data.trans_result.length > 0) {
      return data.trans_result.map(r => r.dst).join('\n');
    }

    return null;
  } catch (err) {
    console.error(`[翻译API] 请求失败: ${err.message}`);
    return null;
  }
}

/**
 * 分段翻译长文本（百度API单次限制6000字节）
 */
async function baiduTranslateLong(text, from = 'auto', to = 'zh') {
  if (!text) return null;

  // 按句号分段，每段不超过4000字符
  const maxLen = 4000;
  const segments = [];
  let current = '';

  const sentences = text.split(/(?<=[.!?。！？\n])\s*/);
  for (const s of sentences) {
    if (current.length + s.length > maxLen && current) {
      segments.push(current);
      current = s;
    } else {
      current += (current ? ' ' : '') + s;
    }
  }
  if (current) segments.push(current);

  const results = [];
  for (const segment of segments) {
    const translated = await baiduTranslate(segment, from, to);
    if (translated === null) return null; // API失败，回退
    results.push(translated);
  }

  return results.join('\n');
}

// ===== 健康领域专业词典（英→中）=====
const HEALTH_DICT = {
  // --- 常见疾病 ---
  'heart disease': '心脏病', 'cardiovascular disease': '心血管疾病',
  'coronary artery disease': '冠心病', 'heart attack': '心肌梗死',
  'heart failure': '心力衰竭', stroke: '中风', hypertension: '高血压',
  'high blood pressure': '高血压', 'low blood pressure': '低血压',
  diabetes: '糖尿病', 'type 2 diabetes': '2型糖尿病', 'type 1 diabetes': '1型糖尿病',
  'blood sugar': '血糖', insulin: '胰岛素', 'insulin resistance': '胰岛素抵抗',
  cancer: '癌症', tumor: '肿瘤', 'breast cancer': '乳腺癌', 'lung cancer': '肺癌',
  'colorectal cancer': '结直肠癌', 'prostate cancer': '前列腺癌',
  'liver cancer': '肝癌', 'stomach cancer': '胃癌', leukemia: '白血病',
  alzheimer: '阿尔茨海默病', "alzheimer's": '阿尔茨海默病',
  "alzheimer's disease": '阿尔茨海默病', dementia: '痴呆症',
  "parkinson's": '帕金森病', "parkinson's disease": '帕金森病',
  arthritis: '关节炎', 'rheumatoid arthritis': '类风湿关节炎',
  osteoarthritis: '骨关节炎', osteoporosis: '骨质疏松症',
  obesity: '肥胖症', overweight: '超重',
  depression: '抑郁症', anxiety: '焦虑症', insomnia: '失眠',
  'sleep apnea': '睡眠呼吸暂停', pneumonia: '肺炎', asthma: '哮喘',
  copd: '慢性阻塞性肺疾病', bronchitis: '支气管炎',
  'kidney disease': '肾病', 'liver disease': '肝病',
  hepatitis: '肝炎', cirrhosis: '肝硬化',
  'atrial fibrillation': '房颤', arrhythmia: '心律失常',
  thrombosis: '血栓', aneurysm: '动脉瘤', atherosclerosis: '动脉粥样硬化',
  inflammation: '炎症', 'chronic inflammation': '慢性炎症',
  infection: '感染', allergy: '过敏', 'autoimmune disease': '自身免疫性疾病',
  gout: '痛风', 'fatty liver': '脂肪肝',
  cataract: '白内障', glaucoma: '青光眼', 'macular degeneration': '黄斑变性',
  'hearing loss': '听力下降', tinnitus: '耳鸣',
  constipation: '便秘', 'irritable bowel': '肠易激综合征',

  // --- 营养与饮食 ---
  protein: '蛋白质', 'amino acid': '氨基酸', vitamin: '维生素',
  'vitamin d': '维生素D', 'vitamin c': '维生素C', 'vitamin b12': '维生素B12',
  'vitamin e': '维生素E', 'folic acid': '叶酸',
  mineral: '矿物质', calcium: '钙', iron: '铁', zinc: '锌',
  magnesium: '镁', potassium: '钾', selenium: '硒',
  fiber: '膳食纤维', 'dietary fiber': '膳食纤维',
  antioxidant: '抗氧化剂', polyphenol: '多酚', flavonoid: '黄酮类',
  'omega-3': 'Omega-3脂肪酸', 'omega 3': 'Omega-3脂肪酸',
  'fish oil': '鱼油', 'olive oil': '橄榄油',
  probiotic: '益生菌', prebiotic: '益生元', 'gut microbiome': '肠道菌群',
  collagen: '胶原蛋白', 'coenzyme q10': '辅酶Q10',
  cholesterol: '胆固醇', 'ldl cholesterol': '低密度脂蛋白胆固醇（坏胆固醇）',
  'hdl cholesterol': '高密度脂蛋白胆固醇（好胆固醇）', triglyceride: '甘油三酯',
  carbohydrate: '碳水化合物', 'whole grain': '全谷物',
  'saturated fat': '饱和脂肪', 'trans fat': '反式脂肪',
  'plant-based': '植物性', 'mediterranean diet': '地中海饮食',
  supplement: '营养补充剂', calorie: '卡路里', metabolism: '新陈代谢',
  'blood glucose': '血糖', 'glycemic index': '升糖指数',

  // --- 医学术语 ---
  'clinical trial': '临床试验', 'randomized controlled trial': '随机对照试验',
  'meta-analysis': '荟萃分析', 'systematic review': '系统综述',
  'peer-reviewed': '同行评审', 'double-blind': '双盲',
  placebo: '安慰剂', biomarker: '生物标志物',
  diagnosis: '诊断', prognosis: '预后', treatment: '治疗',
  therapy: '疗法', 'drug therapy': '药物治疗',
  surgery: '手术', rehabilitation: '康复',
  'side effect': '副作用', 'adverse effect': '不良反应',
  dosage: '剂量', prescription: '处方',
  screening: '筛查', 'early detection': '早期发现',
  vaccine: '疫苗', antibody: '抗体', immunity: '免疫力',
  'immune system': '免疫系统', 'immune response': '免疫反应',
  gene: '基因', genetic: '遗传的', dna: 'DNA',
  'stem cell': '干细胞', chromosome: '染色体',
  'blood pressure': '血压', 'heart rate': '心率', bmi: '身体质量指数(BMI)',

  // --- 运动与康复 ---
  exercise: '运动', 'physical activity': '体力活动',
  'aerobic exercise': '有氧运动', 'resistance training': '抗阻训练',
  'strength training': '力量训练', stretching: '拉伸',
  'tai chi': '太极拳', yoga: '瑜伽', walking: '步行', swimming: '游泳',
  'balance training': '平衡训练', 'fall prevention': '预防跌倒',
  'physical therapy': '物理治疗', 'occupational therapy': '职业治疗',
  'cognitive training': '认知训练',
  flexibility: '柔韧性', endurance: '耐力', 'bone density': '骨密度',
  'muscle mass': '肌肉量', sarcopenia: '肌少症',
  meditation: '冥想', mindfulness: '正念',

  // --- 衰老与抗衰 ---
  aging: '衰老', 'anti-aging': '抗衰老', longevity: '长寿',
  lifespan: '寿命', 'life expectancy': '预期寿命',
  telomere: '端粒', senescence: '细胞衰老',
  'cognitive decline': '认知功能下降', 'memory loss': '记忆力减退',
  'brain health': '大脑健康', neuroplasticity: '神经可塑性',
  'healthy aging': '健康老龄化', 'active aging': '积极老龄化',
  frailty: '衰弱', 'functional decline': '功能减退',

  // --- 研究相关 ---
  study: '研究', research: '研究', findings: '研究发现',
  researchers: '研究人员', scientists: '科学家',
  published: '发表', journal: '期刊', evidence: '证据',
  significant: '显著的', effective: '有效的',
  risk: '风险', 'risk factor': '风险因素', prevention: '预防',
  association: '关联', correlation: '相关性', 'cause and effect': '因果关系',
  participants: '参与者', patients: '患者', subjects: '受试者',
  outcome: '结果', conclusion: '结论', recommendation: '建议',
};

// 按词长度排序（长词优先匹配）
const SORTED_TERMS = Object.entries(HEALTH_DICT)
  .sort((a, b) => b[0].length - a[0].length);

/**
 * 使用内置词典翻译文本中的专业术语
 */
function translateWithDict(text) {
  if (!text) return '';
  let result = text;

  for (const [en, zh] of SORTED_TERMS) {
    const regex = new RegExp(`\\b${escapeRegex(en)}\\b`, 'gi');
    result = result.replace(regex, zh);
  }

  return result;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * 检测文本是否主要是中文
 */
function isChinese(text) {
  if (!text) return false;
  const cn = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  const total = text.replace(/\s/g, '').length;
  return total > 0 && cn / total > 0.3;
}

/**
 * 翻译标题（优先API翻译，降级词典翻译）
 */
async function translateTitle(title) {
  if (!title) return '';

  // 中文标题不需要翻译
  if (isChinese(title)) return title;

  // 尝试API翻译
  if (isBaiduConfigured()) {
    const result = await baiduTranslate(title, 'en', 'zh');
    if (result) return result;
  }

  // 降级：词典翻译
  let translated = translateWithDict(title);
  const chineseChars = (translated.match(/[\u4e00-\u9fff]/g) || []).length;
  if (chineseChars < 4) {
    return `【健康资讯】${translated}`;
  }
  return translated;
}

/**
 * 翻译正文内容（优先API翻译，降级词典翻译）
 */
async function translateContent(content) {
  if (!content) return '';

  // 中文内容不需要翻译
  if (isChinese(content)) return content;

  // 尝试API翻译
  if (isBaiduConfigured()) {
    const result = await baiduTranslateLong(content, 'en', 'zh');
    if (result) return result;
  }

  // 降级：词典翻译
  return translateWithDict(content);
}

/**
 * 生成中文摘要
 */
async function generateChineseSummary(title, content, maxLength = 500) {
  // 先翻译
  const translatedTitle = await translateTitle(title);
  const translatedContent = await translateContent(content);

  const text = `${translatedTitle}。${translatedContent}`;

  // 分句提取
  const sentences = text.split(/[.。！？!?\n]+/)
    .map(s => s.trim())
    .filter(s => s.length > 10);

  if (sentences.length === 0) return text.substring(0, maxLength);

  let summary = '';
  for (const sentence of sentences) {
    if (summary.length + sentence.length > maxLength) break;
    summary += sentence + '。';
  }

  return summary || text.substring(0, maxLength) + '...';
}

/**
 * 提取文章关键要点
 */
function extractKeyPoints(title, content) {
  const text = `${title} ${content}`.toLowerCase();
  const points = [];

  const conclusionPatterns = [
    /(?:study|research|trial|findings?)\s+(?:found|showed?|demonstrated?|revealed?|suggests?|indicates?)\s+(?:that\s+)?(.{20,150})/gi,
    /(?:results?|data|evidence)\s+(?:showed?|suggests?|indicates?)\s+(?:that\s+)?(.{20,150})/gi,
    /(?:may|can|could)\s+(?:help|reduce|prevent|improve|lower|increase)\s+(.{10,100})/gi,
    /(?:associated with|linked to|related to)\s+(.{10,100})/gi,
    /(?:recommended?|advises?|suggests?)\s+(.{10,100})/gi,
  ];

  for (const pattern of conclusionPatterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      let point = translateWithDict(match[0]);
      if (point.length > 15 && points.length < 5) {
        point = point.charAt(0).toUpperCase() + point.slice(1);
        if (!points.some(p => p.includes(point.substring(0, 20)))) {
          points.push(point);
        }
      }
    }
  }

  return points;
}

/**
 * 评估信息来源的可信度等级
 */
function assessCredibility(sourceName, content) {
  const text = `${sourceName} ${content}`.toLowerCase();

  let score = 50;
  const factors = [];

  const authoritative = {
    'nature': 30, 'lancet': 30, 'nejm': 30, 'bmj': 30, 'jama': 30,
    'who': 25, 'nih': 25, 'cdc': 25, 'harvard': 20,
    'mayo clinic': 20, 'johns hopkins': 20, 'oxford': 20,
    'sciencedaily': 15, 'medical news today': 10, 'webmd': 10,
    '人民网': 20, '丁香': 15, '疾控中心': 25, '健康时报': 10,
    'pubmed': 20,
  };

  for (const [source, bonus] of Object.entries(authoritative)) {
    if (text.includes(source)) {
      score += bonus;
      factors.push(`来源权威（${source.toUpperCase()}）`);
      break;
    }
  }

  if (/clinical trial|randomized|controlled trial|double.blind|临床试验|随机对照/i.test(text)) {
    score += 15;
    factors.push('有临床试验支持');
  }

  if (/peer.review|published in|journal|同行评审|发表于/i.test(text)) {
    score += 10;
    factors.push('经同行评审');
  }

  if (/\d+\s*(?:participants?|patients?|subjects?|people|adults|万人|例|名)/i.test(text)) {
    score += 10;
    factors.push('有具体研究数据');
  }

  if (/meta.analysis|systematic review|荟萃分析|系统综述/i.test(text)) {
    score += 15;
    factors.push('荟萃分析/系统综述');
  }

  score = Math.min(100, Math.max(10, score));

  let level, label;
  if (score >= 80) { level = 'high'; label = '高可信度'; }
  else if (score >= 60) { level = 'medium'; label = '中等可信度'; }
  else { level = 'low'; label = '仅供参考'; }

  return { score, level, label, factors };
}

module.exports = {
  translateTitle,
  translateContent,
  translateWithDict,
  generateChineseSummary,
  extractKeyPoints,
  assessCredibility,
  baiduTranslate,
  isBaiduConfigured,
  isChinese,
  HEALTH_DICT,
};
