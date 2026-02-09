const app = getApp();

Page({
  data: {
    categories: [],
    loading: true,
  },

  onLoad() {
    this.loadCategories();
  },

  onShow() {
    this.loadCategories();
  },

  async loadCategories() {
    try {
      const result = await app.request('/categories');
      if (result.success) {
        this.setData({ categories: result.data, loading: false });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
      this.setData({ loading: false });
    }
  },

  onCategoryTap(e) {
    const cat = e.currentTarget.dataset.category;
    wx.switchTab({
      url: '/pages/index/index',
      success() {
        const pages = getCurrentPages();
        const indexPage = pages[pages.length - 1];
        if (indexPage) {
          indexPage.setData({
            currentCategory: cat.id,
            page: 1,
            articles: [],
          });
          indexPage.loadArticles();
        }
      },
    });
  },
});
