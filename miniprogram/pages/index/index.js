const app = getApp();

Page({
  data: {
    articles: [],
    categories: [],
    currentCategory: 'all',
    page: 1,
    totalPages: 1,
    loading: false,
    hasMore: true,
    featured: null,
  },

  onLoad() {
    this.loadCategories();
    this.loadArticles();
  },

  onPullDownRefresh() {
    this.setData({ page: 1, articles: [] });
    this.loadArticles().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 });
      this.loadArticles(true);
    }
  },

  async loadArticles(append = false) {
    if (this.data.loading) return;
    this.setData({ loading: true });

    try {
      const params = `?page=${this.data.page}&limit=20`;
      const catParam =
        this.data.currentCategory !== 'all' ? `&category=${this.data.currentCategory}` : '';
      const result = await app.request(`/articles${params}${catParam}`);

      if (result.success) {
        const { articles, pagination } = result.data;
        const featured = !append && articles.length > 0 ? articles[0] : this.data.featured;

        this.setData({
          articles: append ? [...this.data.articles, ...articles] : articles,
          totalPages: pagination.totalPages,
          hasMore: this.data.page < pagination.totalPages,
          featured,
        });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  async loadCategories() {
    try {
      const result = await app.request('/categories');
      if (result.success) {
        this.setData({ categories: [{ id: 'all', name: '全部', icon: '📋' }, ...result.data] });
      }
    } catch (err) {
      console.error('加载分类失败:', err);
    }
  },

  onCategoryTap(e) {
    const category = e.currentTarget.dataset.id;
    this.setData({
      currentCategory: category,
      page: 1,
      articles: [],
    });
    this.loadArticles();
  },

  onArticleTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/article/article?id=${id}` });
  },

  onSearch() {
    wx.showModal({
      title: '搜索',
      editable: true,
      placeholderText: '输入关键词搜索健康资讯',
      success: (res) => {
        if (res.confirm && res.content) {
          // 跳转搜索结果
          this.setData({ page: 1, articles: [] });
          this.loadArticles();
        }
      },
    });
  },
});
