/**
 * 乐龄健康资讯平台 - 前端主逻辑
 */
(function () {
  'use strict';

  // ===== 应用状态 =====
  const state = {
    currentView: 'list', // list | detail
    currentTab: 'home',
    currentCategory: 'all',
    articles: [],
    currentArticle: null,
    categories: [],
    page: 1,
    totalPages: 1,
    loading: false,
    searchActive: false,
    searchQuery: '',
    userStats: {
      read: 0,
      liked: 0,
      shared: 0,
    },
    likedArticles: new Set(),
  };

  // ===== DOM 元素缓存 =====
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const els = {
    headerTitle: $('#headerTitle'),
    searchBar: $('#searchBar'),
    searchInput: $('#searchInput'),
    categoryNav: $('#categoryNav'),
    categoryScroll: $('.category-scroll'),
    mainContent: $('#mainContent'),
    viewList: $('#viewList'),
    viewDetail: $('#viewDetail'),
    featuredCard: $('#featuredCard'),
    featuredSection: $('#featuredSection'),
    articleList: $('#articleList'),
    articleDetail: $('#articleDetail'),
    loadMore: $('#loadMore'),
    btnLoadMore: $('#btnLoadMore'),
    tabBar: $('#tabBar'),
    categoryGrid: $('#categoryGrid'),
    trendingList: $('#trendingList'),
    toast: $('#toast'),
  };

  // ===== 分类名称映射（匹配后端config.js） =====
  const categoryNames = {
    chronic_disease: '慢病管理',
    nutrition: '饮食营养',
    elderly_care: '乐龄健康',
    fitness: '运动康健',
    medical_research: '医学前沿',
    disease_prevention: '疾病预防',
    mental_health: '心理健康',
    traditional_medicine: '中医养生',
    rehabilitation: '康复护理',
    wellness: '养生保健',
    public_health: '公共卫生',
  };

  // ===== 可信度标签映射 =====
  const credibilityLabels = {
    high: '高可信',
    medium: '一般',
    low: '待验证',
  };

  // ===== 初始化 =====
  function init() {
    loadUserData();
    bindEvents();
    loadCategories();
    loadArticles();
  }

  // ===== 事件绑定 =====
  function bindEvents() {
    // 搜索
    $('#btnSearch').addEventListener('click', toggleSearch);
    $('#btnSearchCancel').addEventListener('click', toggleSearch);
    els.searchInput.addEventListener('input', debounce(handleSearch, 500));

    // 刷新
    $('#btnRefresh').addEventListener('click', refreshArticles);

    // 加载更多
    els.btnLoadMore.addEventListener('click', loadMoreArticles);

    // 底部标签栏
    $$('.tab-item').forEach((tab) => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // 子页面返回按钮
    $('#btnBackFromCats').addEventListener('click', () => closePage('pageCats'));
    $('#btnBackFromTrending').addEventListener('click', () => closePage('pageTrending'));
    $('#btnBackFromProfile').addEventListener('click', () => closePage('pageProfile'));

    // 字体大小
    $('#btnFontSmall').addEventListener('click', () => setFontSize('small'));
    $('#btnFontMedium').addEventListener('click', () => setFontSize('medium'));
    $('#btnFontLarge').addEventListener('click', () => setFontSize('large'));
    $('#btnFontXlarge').addEventListener('click', () => setFontSize('xlarge'));
  }

  // ===== 数据加载 =====
  async function loadArticles(append = false) {
    if (state.loading) return;
    state.loading = true;

    if (!append) {
      els.articleList.innerHTML = `
        <div class="skeleton skeleton-article"></div>
        <div class="skeleton skeleton-article"></div>
        <div class="skeleton skeleton-article"></div>
      `;
    }

    els.btnLoadMore.classList.add('loading');
    els.btnLoadMore.textContent = '加载中...';

    try {
      const result = await API.getArticles({
        page: state.page,
        limit: 20,
        category: state.currentCategory,
        search: state.searchQuery,
      });

      if (result.success) {
        const { articles, pagination } = result.data;
        state.totalPages = pagination.totalPages;

        if (append) {
          state.articles = [...state.articles, ...articles];
        } else {
          state.articles = articles;
        }

        renderArticles(append);
        renderFeatured();

        // 更新加载更多按钮
        if (state.page >= state.totalPages) {
          els.btnLoadMore.textContent = '没有更多了';
          els.btnLoadMore.disabled = true;
        } else {
          els.btnLoadMore.textContent = '加载更多';
          els.btnLoadMore.disabled = false;
        }
      }
    } catch (err) {
      if (!append) {
        els.articleList.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">📡</div>
            <div class="empty-text">暂时无法获取资讯</div>
            <div class="empty-hint">请检查网络连接后重试，或点击右上角刷新按钮触发数据采集</div>
          </div>
        `;
      }
      els.btnLoadMore.textContent = '加载失败，点击重试';
    } finally {
      state.loading = false;
      els.btnLoadMore.classList.remove('loading');
    }
  }

  async function loadCategories() {
    try {
      const result = await API.getCategories();
      if (result.success) {
        state.categories = result.data;
        renderCategoryNav();
        renderCategoryGrid();
      }
    } catch (err) {
      console.error('加载分类失败:', err);
    }
  }

  // ===== 渲染函数 =====
  function renderArticles(append = false) {
    if (state.articles.length === 0 && !append) {
      els.articleList.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">暂无资讯内容</div>
          <div class="empty-hint">点击右上角刷新按钮开始采集最新健康资讯</div>
        </div>
      `;
      return;
    }

    const articlesToRender = append ? state.articles.slice(-20) : state.articles;
    const startIndex = append ? state.articles.length - articlesToRender.length : 0;

    if (!append) {
      els.articleList.innerHTML = '';
    }

    // 跳过第一篇（已显示在推荐区）
    const list = startIndex === 0 ? articlesToRender.slice(1) : articlesToRender;

    list.forEach((article) => {
      const card = createArticleCard(article);
      els.articleList.appendChild(card);
    });
  }

  function renderFeatured() {
    if (state.articles.length === 0) {
      els.featuredSection.style.display = 'none';
      return;
    }

    els.featuredSection.style.display = 'block';
    const article = state.articles[0];
    const catName = categoryNames[article.category] || '健康资讯';

    els.featuredCard.innerHTML = `
      <div class="featured-category">${catName}</div>
      <div class="featured-title">${escapeHtml(article.title || article.original_title || '')}</div>
      <div class="featured-summary">${escapeHtml(article.summary || '')}</div>
      <div class="featured-meta">
        <span>${article.source_name || ''}</span>
        <span>${formatDate(article.published_at)}</span>
      </div>
    `;

    els.featuredCard.onclick = () => showArticleDetail(article.id);
  }

  function createArticleCard(article) {
    const card = document.createElement('div');
    card.className = 'article-card';
    const catName = categoryNames[article.category] || '健康资讯';

    // 可信度徽章
    let credBadge = '';
    if (article.credibility_level) {
      const level = article.credibility_level;
      const label = credibilityLabels[level] || level;
      credBadge = `<span class="credibility-badge ${level}">${label}</span>`;
    }

    // 标签
    let tagsHtml = '';
    if (article.tags && article.tags.length > 0) {
      const visibleTags = article.tags.slice(0, 3);
      tagsHtml = `<div class="article-tags">${visibleTags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join('')}</div>`;
    }

    // 关键要点预览（取第一条）
    let keypointHtml = '';
    if (article.key_points && article.key_points.length > 0) {
      keypointHtml = `<div class="article-keypoint">${escapeHtml(article.key_points[0])}</div>`;
    }

    card.innerHTML = `
      <div class="article-header-row">
        <span class="article-category">${catName}</span>
        ${credBadge}
      </div>
      <h3 class="article-title">${escapeHtml(article.title || article.original_title || '')}</h3>
      <p class="article-summary">${escapeHtml(article.summary || '')}</p>
      ${keypointHtml}
      ${tagsHtml}
      <div class="article-meta">
        <span>${article.source_name || ''} · ${formatDate(article.published_at)}</span>
        <div class="article-stats">
          <span>${article.view_count || 0} 阅读</span>
          <span>${article.like_count || 0} 赞</span>
        </div>
      </div>
    `;

    card.addEventListener('click', () => showArticleDetail(article.id));
    return card;
  }

  function renderCategoryNav() {
    const scroll = els.categoryScroll;
    scroll.innerHTML = '<button class="category-tab active" data-category="all">全部</button>';

    state.categories.forEach((cat) => {
      const btn = document.createElement('button');
      btn.className = 'category-tab';
      btn.dataset.category = cat.id;
      btn.textContent = `${cat.icon} ${cat.name}`;
      scroll.appendChild(btn);
    });

    // 绑定分类切换事件
    scroll.querySelectorAll('.category-tab').forEach((tab) => {
      tab.addEventListener('click', () => {
        scroll.querySelectorAll('.category-tab').forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        state.currentCategory = tab.dataset.category;
        state.page = 1;
        loadArticles();
      });
    });
  }

  function renderCategoryGrid() {
    const grid = els.categoryGrid;
    grid.innerHTML = '';

    state.categories.forEach((cat) => {
      const card = document.createElement('div');
      card.className = 'category-card';
      card.innerHTML = `
        <div class="cat-icon">${cat.icon}</div>
        <div class="cat-name">${cat.name}</div>
        <div class="cat-desc">${cat.description}</div>
        <div class="cat-count">${cat.articleCount || 0} 篇文章</div>
      `;
      card.addEventListener('click', () => {
        closePage('pageCats');
        state.currentCategory = cat.id;
        state.page = 1;

        // 更新顶部分类导航的选中状态
        els.categoryScroll.querySelectorAll('.category-tab').forEach((tab) => {
          tab.classList.toggle('active', tab.dataset.category === cat.id);
        });

        loadArticles();
        switchTab('home');
      });
      grid.appendChild(card);
    });
  }

  // ===== 文章详情 =====
  async function showArticleDetail(id) {
    state.currentView = 'detail';
    els.viewList.classList.remove('active');
    els.viewDetail.classList.add('active');
    els.categoryNav.style.display = 'none';

    els.articleDetail.innerHTML = `
      <div class="skeleton" style="height: 30px; width: 60%; margin-bottom: 12px;"></div>
      <div class="skeleton" style="height: 20px; width: 40%; margin-bottom: 24px;"></div>
      <div class="skeleton" style="height: 200px; margin-bottom: 12px;"></div>
    `;

    try {
      const result = await API.getArticle(id);
      if (result.success) {
        state.currentArticle = result.data;
        renderArticleDetail(result.data);

        // 更新阅读统计
        state.userStats.read++;
        saveUserData();
      }
    } catch (err) {
      els.articleDetail.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">😔</div>
          <div class="empty-text">文章加载失败</div>
          <div class="empty-hint">请返回重试</div>
        </div>
      `;
    }
  }

  function renderArticleDetail(article) {
    const catName = categoryNames[article.category] || '健康资讯';
    const isLiked = state.likedArticles.has(article.id);

    // 处理内容分段
    const contentParagraphs = (article.content || article.original_content || '')
      .split('\n')
      .filter((p) => p.trim())
      .map((p) => `<p>${escapeHtml(p)}</p>`)
      .join('');

    // 可信度卡片
    let credibilityHtml = '';
    if (article.credibility_score || article.credibility_level) {
      const score = article.credibility_score || 0;
      const level = article.credibility_level || 'medium';
      const label = credibilityLabels[level] || level;
      const factors = article.credibility_factors || [];

      credibilityHtml = `
        <div class="credibility-card">
          <div class="cred-header">
            信息可信度评估
            <span class="cred-score ${level}">${score}分 - ${label}</span>
          </div>
          ${factors.length > 0 ? `
            <ul class="cred-factors">
              ${factors.map((f) => `<li>${escapeHtml(f)}</li>`).join('')}
            </ul>
          ` : ''}
        </div>
      `;
    }

    // 关键要点
    let keyPointsHtml = '';
    if (article.key_points && article.key_points.length > 0) {
      keyPointsHtml = `
        <div class="key-points">
          <div class="kp-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            核心要点
          </div>
          <ul class="kp-list">
            ${article.key_points.map((kp, i) => `<li data-num="${i + 1}">${escapeHtml(kp)}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    // 健康提示
    let tipsHtml = '';
    if (article.health_tips && article.health_tips.length > 0) {
      tipsHtml = `
        <div class="health-tips">
          <div class="tips-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
              <path d="M12 16v-4"/><path d="M12 8h.01"/>
            </svg>
            健康小贴士
          </div>
          <ul class="tips-list">
            ${article.health_tips.map((tip) => `<li>${escapeHtml(tip)}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    // 标签
    let tagsHtml = '';
    if (article.tags && article.tags.length > 0) {
      tagsHtml = `<div class="article-tags" style="margin-bottom: 16px;">
        ${article.tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
      </div>`;
    }

    els.articleDetail.innerHTML = `
      <div class="detail-back" id="detailBack">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m15 18-6-6 6-6"/>
        </svg>
        返回列表
      </div>

      <span class="detail-category">${catName}</span>
      <h1 class="detail-title">${escapeHtml(article.title || article.original_title || '')}</h1>

      <div class="detail-meta">
        <span>来源: ${escapeHtml(article.source_name || '未知')}</span>
        <span>发布: ${formatDate(article.published_at)}</span>
        <span>${article.view_count || 0} 次阅读</span>
      </div>

      ${credibilityHtml}
      ${keyPointsHtml}
      ${tagsHtml}

      <div class="detail-content">
        ${contentParagraphs || '<p>暂无详细内容</p>'}
      </div>

      ${tipsHtml}

      <div class="medical-disclaimer">
        <strong>声明：</strong>本文内容仅供健康科普参考，不构成任何医疗诊断或治疗建议。如有健康问题，请及时就医咨询专业医生。
      </div>

      <div class="article-actions">
        <button class="action-btn ${isLiked ? 'liked' : ''}" id="btnLike" data-id="${article.id}">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="${isLiked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          <span>${article.like_count || 0} 赞</span>
        </button>
        <button class="action-btn" id="btnShare" data-id="${article.id}">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
          </svg>
          <span>分享</span>
        </button>
      </div>

      ${
        article.original_link
          ? `<a class="original-link" href="${escapeHtml(article.original_link)}" target="_blank" rel="noopener">查看原文链接</a>`
          : ''
      }
    `;

    // 绑定事件
    $('#detailBack').addEventListener('click', backToList);
    $('#btnLike').addEventListener('click', () => handleLike(article.id));
    $('#btnShare').addEventListener('click', () => handleShare(article.id));

    // 滚动到顶部
    els.mainContent.scrollTop = 0;
  }

  function backToList() {
    state.currentView = 'list';
    els.viewDetail.classList.remove('active');
    els.viewList.classList.add('active');
    els.categoryNav.style.display = '';
    els.headerTitle.textContent = '乐龄健康';
  }

  // ===== 交互处理 =====
  async function handleLike(articleId) {
    try {
      const result = await API.likeArticle(articleId);
      if (result.success) {
        state.likedArticles.add(articleId);
        state.userStats.liked++;
        saveUserData();
        showToast('点赞成功');

        // 更新 UI
        const btn = $('#btnLike');
        if (btn) {
          btn.classList.add('liked');
          const svg = btn.querySelector('svg');
          if (svg) svg.setAttribute('fill', 'currentColor');
          const span = btn.querySelector('span');
          if (span) span.textContent = `${result.data.like_count} 赞`;
        }
      }
    } catch (err) {
      showToast('操作失败，请重试');
    }
  }

  async function handleShare(articleId) {
    const article = state.currentArticle;
    const shareData = {
      title: article ? article.title : '乐龄健康',
      text: article ? article.summary : '',
      url: window.location.href,
    };

    // 尝试使用原生分享 API
    if (navigator.share) {
      try {
        await navigator.share(shareData);
        await API.shareArticle(articleId);
        state.userStats.shared++;
        saveUserData();
      } catch (err) {
        if (err.name !== 'AbortError') {
          fallbackShare(shareData);
        }
      }
    } else {
      fallbackShare(shareData);
    }
  }

  function fallbackShare(shareData) {
    // 复制链接到剪贴板
    const text = `${shareData.title}\n${shareData.text}\n${shareData.url}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        showToast('链接已复制到剪贴板');
      });
    } else {
      showToast('请手动复制链接分享');
    }
  }

  function toggleSearch() {
    state.searchActive = !state.searchActive;
    els.searchBar.classList.toggle('active', state.searchActive);

    if (state.searchActive) {
      els.searchInput.focus();
    } else {
      els.searchInput.value = '';
      state.searchQuery = '';
      state.page = 1;
      loadArticles();
    }
  }

  function handleSearch() {
    state.searchQuery = els.searchInput.value.trim();
    state.page = 1;
    loadArticles();
  }

  function refreshArticles() {
    showToast('正在刷新...');
    state.page = 1;
    loadArticles();
  }

  function loadMoreArticles() {
    if (state.page < state.totalPages && !state.loading) {
      state.page++;
      loadArticles(true);
    }
  }

  // ===== 标签切换 =====
  function switchTab(tab) {
    state.currentTab = tab;

    // 更新标签栏状态
    $$('.tab-item').forEach((item) => {
      item.classList.toggle('active', item.dataset.tab === tab);
    });

    // 页面显示逻辑
    switch (tab) {
      case 'home':
        closeAllPages();
        if (state.currentView === 'detail') {
          backToList();
        }
        break;
      case 'categories':
        openPage('pageCats');
        loadCategories();
        break;
      case 'trending':
        openPage('pageTrending');
        loadTrending();
        break;
      case 'profile':
        openPage('pageProfile');
        updateProfileStats();
        break;
    }
  }

  function openPage(pageId) {
    closeAllPages();
    $(`#${pageId}`).classList.add('active');
  }

  function closePage(pageId) {
    $(`#${pageId}`).classList.remove('active');
    switchTab('home');
  }

  function closeAllPages() {
    $$('.page').forEach((p) => p.classList.remove('active'));
  }

  // ===== 热门页面 =====
  async function loadTrending() {
    const list = els.trendingList;
    list.innerHTML = `
      <div class="skeleton skeleton-article"></div>
      <div class="skeleton skeleton-article"></div>
    `;

    try {
      const result = await API.getArticles({ sort: 'popular', limit: 20 });
      if (result.success && result.data.articles.length > 0) {
        list.innerHTML = '';
        result.data.articles.forEach((article) => {
          list.appendChild(createArticleCard(article));
        });
      } else {
        list.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">📊</div>
            <div class="empty-text">暂无热门资讯</div>
            <div class="empty-hint">资讯采集后将在此展示热门内容</div>
          </div>
        `;
      }
    } catch (err) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">😔</div>
          <div class="empty-text">加载失败</div>
        </div>
      `;
    }
  }

  // ===== 字体大小 =====
  function setFontSize(size) {
    document.body.classList.remove('font-small', 'font-medium', 'font-large', 'font-xlarge');
    if (size !== 'large') {
      // 默认是大号（:root已设为大字号），其他需要class
      document.body.classList.add(`font-${size}`);
    }

    // 更新按钮状态
    $$('.btn-font').forEach((btn) => btn.classList.remove('active'));
    const btnId = `#btnFont${size.charAt(0).toUpperCase() + size.slice(1)}`;
    const btn = $(btnId);
    if (btn) btn.classList.add('active');

    localStorage.setItem('fontSize', size);

    const sizeLabels = { small: '小', medium: '中', large: '大', xlarge: '特大' };
    showToast(`已切换为${sizeLabels[size] || size}字号`);
  }

  // ===== 用户数据持久化 =====
  function loadUserData() {
    try {
      const stats = localStorage.getItem('userStats');
      if (stats) state.userStats = JSON.parse(stats);

      const liked = localStorage.getItem('likedArticles');
      if (liked) state.likedArticles = new Set(JSON.parse(liked));

      const fontSize = localStorage.getItem('fontSize') || 'large';
      if (fontSize !== 'large') {
        document.body.classList.add(`font-${fontSize}`);
      }
      // 更新字体按钮状态
      const btnId = `#btnFont${fontSize.charAt(0).toUpperCase() + fontSize.slice(1)}`;
      const btn = $(btnId);
      if (btn) {
        $$('.btn-font').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
      }
    } catch (err) {
      console.error('加载用户数据失败:', err);
    }
  }

  function saveUserData() {
    try {
      localStorage.setItem('userStats', JSON.stringify(state.userStats));
      localStorage.setItem('likedArticles', JSON.stringify([...state.likedArticles]));
    } catch (err) {
      console.error('保存用户数据失败:', err);
    }
  }

  function updateProfileStats() {
    $('#statRead').textContent = state.userStats.read;
    $('#statLiked').textContent = state.userStats.liked;
    $('#statShared').textContent = state.userStats.shared;
  }

  // ===== 工具函数 =====
  function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now - date;

      if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return minutes <= 0 ? '刚刚' : `${minutes}分钟前`;
      }
      if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`;
      }
      if (diff < 604800000) {
        return `${Math.floor(diff / 86400000)}天前`;
      }

      const month = date.getMonth() + 1;
      const day = date.getDate();
      return date.getFullYear() === now.getFullYear()
        ? `${month}月${day}日`
        : `${date.getFullYear()}年${month}月${day}日`;
    } catch {
      return dateStr;
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function showToast(message, duration = 2000) {
    els.toast.textContent = message;
    els.toast.classList.add('active');
    setTimeout(() => {
      els.toast.classList.remove('active');
    }, duration);
  }

  function debounce(fn, delay) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  // ===== 启动应用 =====
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
