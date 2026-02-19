/**
 * API 客户端 - 健康资讯聚合平台
 */
const API = {
  baseURL: '/api',

  /**
   * 通用请求方法
   */
  async request(path, options = {}) {
    const url = `${this.baseURL}${path}`;
    try {
      const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error(`[API] ${path} 请求出错:`, err.message);
      throw err;
    }
  },

  /**
   * 获取文章列表
   */
  async getArticles({ page = 1, limit = 20, category, search, sort } = {}) {
    const params = new URLSearchParams();
    params.set('page', page);
    params.set('limit', limit);
    if (category && category !== 'all') params.set('category', category);
    if (search) params.set('search', search);
    if (sort) params.set('sort', sort);

    return this.request(`/articles?${params.toString()}`);
  },

  /**
   * 获取文章详情
   */
  async getArticle(id) {
    return this.request(`/articles/${id}`);
  },

  /**
   * 点赞文章
   */
  async likeArticle(id) {
    return this.request(`/articles/${id}/like`, { method: 'POST' });
  },

  /**
   * 分享文章
   */
  async shareArticle(id) {
    return this.request(`/articles/${id}/share`, { method: 'POST' });
  },

  /**
   * 获取分类列表
   */
  async getCategories() {
    return this.request('/categories');
  },

  /**
   * 获取系统统计
   */
  async getStats() {
    return this.request('/admin/stats');
  },

  /**
   * 手动触发采集
   */
  async triggerAggregation() {
    return this.request('/admin/aggregate', { method: 'POST' });
  },

  /**
   * 健康检查
   */
  async healthCheck() {
    return this.request('/health');
  },
};
