const app = getApp();

Page({
  data: {
    articles: [],
    loading: true,
  },

  onLoad() {
    this.loadTrending();
  },

  onShow() {
    this.loadTrending();
  },

  onPullDownRefresh() {
    this.loadTrending().then(() => wx.stopPullDownRefresh());
  },

  async loadTrending() {
    this.setData({ loading: true });
    try {
      const result = await app.request('/articles?sort=popular&limit=30');
      if (result.success) {
        this.setData({
          articles: result.data.articles,
          loading: false,
        });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
      this.setData({ loading: false });
    }
  },

  onArticleTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/article/article?id=${id}` });
  },
});
