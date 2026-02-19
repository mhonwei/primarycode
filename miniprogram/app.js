/**
 * 健康资讯聚合平台 - 微信小程序入口
 */
App({
  globalData: {
    // 后端 API 地址（部署后替换为实际地址）
    apiBaseUrl: 'https://your-server-domain.com/api',

    // 用户信息
    userInfo: null,

    // 字体大小设置
    fontSize: 'medium',

    // 用户统计
    userStats: {
      read: 0,
      liked: 0,
      shared: 0,
    },

    // 已点赞文章
    likedArticles: [],
  },

  onLaunch() {
    // 加载本地存储的用户设置
    this.loadUserSettings();
  },

  /**
   * 加载用户设置
   */
  loadUserSettings() {
    try {
      const fontSize = wx.getStorageSync('fontSize');
      if (fontSize) this.globalData.fontSize = fontSize;

      const userStats = wx.getStorageSync('userStats');
      if (userStats) this.globalData.userStats = JSON.parse(userStats);

      const likedArticles = wx.getStorageSync('likedArticles');
      if (likedArticles) this.globalData.likedArticles = JSON.parse(likedArticles);
    } catch (e) {
      console.error('加载设置失败:', e);
    }
  },

  /**
   * 保存用户设置
   */
  saveUserSettings() {
    try {
      wx.setStorageSync('fontSize', this.globalData.fontSize);
      wx.setStorageSync('userStats', JSON.stringify(this.globalData.userStats));
      wx.setStorageSync('likedArticles', JSON.stringify(this.globalData.likedArticles));
    } catch (e) {
      console.error('保存设置失败:', e);
    }
  },

  /**
   * 通用 API 请求
   */
  request(path, options = {}) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${this.globalData.apiBaseUrl}${path}`,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Content-Type': 'application/json',
        },
        success(res) {
          if (res.statusCode === 200) {
            resolve(res.data);
          } else {
            reject(new Error(`请求失败: ${res.statusCode}`));
          }
        },
        fail(err) {
          reject(err);
        },
      });
    });
  },
});
