const app = getApp();

Page({
  data: {
    article: null,
    loading: true,
    isLiked: false,
  },

  onLoad(options) {
    if (options.id) {
      this.loadArticle(options.id);
    }
  },

  async loadArticle(id) {
    try {
      const result = await app.request(`/articles/${id}`);
      if (result.success) {
        const article = result.data;
        const isLiked = app.globalData.likedArticles.includes(article.id);

        this.setData({
          article,
          loading: false,
          isLiked,
        });

        // 更新阅读计数
        app.globalData.userStats.read++;
        app.saveUserSettings();

        // 设置页面标题
        wx.setNavigationBarTitle({
          title: article.title || '文章详情',
        });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
      this.setData({ loading: false });
    }
  },

  async onLike() {
    if (!this.data.article) return;
    const id = this.data.article.id;

    try {
      const result = await app.request(`/articles/${id}/like`, { method: 'POST' });
      if (result.success) {
        this.setData({
          isLiked: true,
          'article.like_count': result.data.like_count,
        });

        if (!app.globalData.likedArticles.includes(id)) {
          app.globalData.likedArticles.push(id);
        }
        app.globalData.userStats.liked++;
        app.saveUserSettings();

        wx.showToast({ title: '点赞成功', icon: 'success' });
      }
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },

  onShare() {
    if (!this.data.article) return;
    const id = this.data.article.id;

    app.request(`/articles/${id}/share`, { method: 'POST' }).catch(() => {});
    app.globalData.userStats.shared++;
    app.saveUserSettings();
  },

  onShareAppMessage() {
    const article = this.data.article;
    return {
      title: article ? article.title : '健康资讯推荐',
      path: `/pages/article/article?id=${article ? article.id : ''}`,
    };
  },

  onViewOriginal() {
    if (this.data.article && this.data.article.original_link) {
      wx.setClipboardData({
        data: this.data.article.original_link,
        success() {
          wx.showToast({ title: '原文链接已复制', icon: 'success' });
        },
      });
    }
  },
});
