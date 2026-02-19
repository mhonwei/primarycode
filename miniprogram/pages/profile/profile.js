const app = getApp();

Page({
  data: {
    userStats: { read: 0, liked: 0, shared: 0 },
    fontSize: 'medium',
  },

  onShow() {
    this.setData({
      userStats: app.globalData.userStats,
      fontSize: app.globalData.fontSize,
    });
  },

  onFontSize(e) {
    const size = e.currentTarget.dataset.size;
    app.globalData.fontSize = size;
    app.saveUserSettings();
    this.setData({ fontSize: size });
    wx.showToast({
      title: `已切换为${size === 'small' ? '小' : size === 'large' ? '大' : '中'}字号`,
      icon: 'success',
    });
  },

  onAbout() {
    wx.showModal({
      title: '关于健康资讯',
      content:
        '健康资讯聚合平台 v1.0.0\n\n每日精选健康、养生、科学研究资讯，为您提供科学可靠的健康信息服务。\n\n温馨提示：本平台内容仅供参考，不构成医疗建议。',
      showCancel: false,
    });
  },
});
