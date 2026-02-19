/**
 * 微信公众号推送服务
 *
 * 功能：
 * 1. 获取 access_token
 * 2. 创建图文素材
 * 3. 群发文章到公众号
 * 4. 定时推送每日精选
 *
 * 配置（环境变量）：
 *   WECHAT_APPID=你的公众号AppID
 *   WECHAT_SECRET=你的公众号AppSecret
 *
 * 获取方式：
 *   微信公众平台 (mp.weixin.qq.com) → 设置与开发 → 基本配置
 *
 * 注意：
 *   - 认证的服务号才能群发消息（订阅号每天可发1次）
 *   - 需在公众号后台设置服务器IP白名单
 */

const { getDatabase } = require('../database');

const WECHAT_APPID = process.env.WECHAT_APPID || '';
const WECHAT_SECRET = process.env.WECHAT_SECRET || '';
const WECHAT_API = 'https://api.weixin.qq.com/cgi-bin';

let accessToken = '';
let tokenExpiry = 0;

/**
 * 检查是否配置了微信公众号
 */
function isWechatConfigured() {
  return WECHAT_APPID && WECHAT_SECRET;
}

/**
 * 获取 access_token（带缓存）
 */
async function getAccessToken() {
  if (accessToken && Date.now() < tokenExpiry) {
    return accessToken;
  }

  const url = `${WECHAT_API}/token?grant_type=client_credential&appid=${WECHAT_APPID}&secret=${WECHAT_SECRET}`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    if (data.errcode) {
      console.error(`[微信] 获取token失败: ${data.errcode} - ${data.errmsg}`);
      return null;
    }

    accessToken = data.access_token;
    tokenExpiry = Date.now() + (data.expires_in - 300) * 1000; // 提前5分钟过期
    return accessToken;
  } catch (err) {
    console.error(`[微信] 获取token请求失败: ${err.message}`);
    return null;
  }
}

/**
 * 将文章格式化为微信图文消息格式
 */
function formatArticleForWechat(article) {
  // 构建正文HTML
  let body = '';

  // 可信度信息
  if (article.credibility_level) {
    const colors = { high: '#27ae60', medium: '#f39c12', low: '#e74c3c' };
    const labels = { high: '高可信度', medium: '中等可信度', low: '仅供参考' };
    body += `<p style="background:#f8f9fa;padding:10px;border-radius:8px;color:${colors[article.credibility_level] || '#666'}">📊 信息可信度：${labels[article.credibility_level] || ''} ${article.credibility_score || 0}分</p>`;
  }

  // 正文
  const content = (article.content || '')
    .split('\n')
    .filter(p => p.trim())
    .map(p => `<p>${p}</p>`)
    .join('');
  body += content;

  // 健康提示
  let tips = [];
  try { tips = JSON.parse(article.health_tips || '[]'); } catch { /* ignore */ }
  if (tips.length > 0) {
    body += '<section style="background:#fef3c7;padding:15px;border-radius:8px;margin-top:15px;">';
    body += '<p style="font-weight:bold;color:#92400e;">💡 健康小贴士</p>';
    tips.forEach(tip => {
      body += `<p style="color:#78350f;">✅ ${tip}</p>`;
    });
    body += '</section>';
  }

  // 声明
  body += '<p style="font-size:12px;color:#999;margin-top:20px;">声明：本文内容仅供健康科普参考，不构成医疗诊断或治疗建议。如有健康问题，请及时就医咨询专业医生。</p>';

  return {
    title: article.title || article.original_title || '健康资讯',
    digest: (article.summary || '').substring(0, 120),
    content: body,
    content_source_url: article.original_link || '',
    show_cover_pic: 0,
  };
}

/**
 * 上传图文素材（永久素材）
 */
async function uploadArticles(articles) {
  const token = await getAccessToken();
  if (!token) return null;

  const wxArticles = articles.map(formatArticleForWechat);

  const url = `${WECHAT_API}/material/add_news?access_token=${token}`;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ articles: wxArticles }),
    });

    const data = await res.json();
    if (data.errcode) {
      console.error(`[微信] 上传素材失败: ${data.errcode} - ${data.errmsg}`);
      return null;
    }

    console.log(`[微信] 图文素材上传成功, media_id: ${data.media_id}`);
    return data.media_id;
  } catch (err) {
    console.error(`[微信] 上传素材请求失败: ${err.message}`);
    return null;
  }
}

/**
 * 群发图文消息给所有关注者
 */
async function sendToAll(mediaId) {
  const token = await getAccessToken();
  if (!token) return null;

  const url = `${WECHAT_API}/message/mass/sendall?access_token=${token}`;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filter: { is_to_all: true },
        mpnews: { media_id: mediaId },
        msgtype: 'mpnews',
        send_ignore_reprint: 1,
      }),
    });

    const data = await res.json();
    if (data.errcode && data.errcode !== 0) {
      console.error(`[微信] 群发失败: ${data.errcode} - ${data.errmsg}`);
      return null;
    }

    console.log(`[微信] 群发成功, msg_id: ${data.msg_id}`);
    return data.msg_id;
  } catch (err) {
    console.error(`[微信] 群发请求失败: ${err.message}`);
    return null;
  }
}

/**
 * 每日精选推送：选取当天最佳文章推送到公众号
 */
async function pushDailyDigest(count = 5) {
  if (!isWechatConfigured()) {
    console.log('[微信] 未配置公众号信息，跳过推送');
    return { success: false, message: '未配置微信公众号' };
  }

  console.log('[微信] 正在准备每日精选推送...');

  const db = getDatabase();

  // 选取今天可信度最高、阅读量最高的文章
  const articles = db.prepare(`
    SELECT * FROM articles
    WHERE status = 'transformed'
      AND transformed_at > datetime('now', '-1 day')
    ORDER BY credibility_score DESC, view_count DESC
    LIMIT ?
  `).all(count);

  if (articles.length === 0) {
    console.log('[微信] 没有新文章可推送');
    return { success: false, message: '没有新文章' };
  }

  // 解析JSON字段
  const parsed = articles.map(a => ({
    ...a,
    health_tips: a.health_tips || '[]',
  }));

  console.log(`[微信] 选取了 ${parsed.length} 篇文章准备推送`);

  // 上传图文素材
  const mediaId = await uploadArticles(parsed);
  if (!mediaId) {
    return { success: false, message: '素材上传失败' };
  }

  // 群发
  const msgId = await sendToAll(mediaId);
  if (!msgId) {
    return { success: false, message: '群发失败' };
  }

  return { success: true, message: `推送成功，共 ${parsed.length} 篇`, msgId };
}

module.exports = {
  isWechatConfigured,
  getAccessToken,
  uploadArticles,
  sendToAll,
  pushDailyDigest,
  formatArticleForWechat,
};
