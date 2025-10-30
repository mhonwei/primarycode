import React, { useState } from 'react';
import '../styles/SearchPanel.css';

function SearchPanel({ onSearch, loading }) {
  const [keyword, setKeyword] = useState('');
  const [searchType, setSearchType] = useState('all');
  const [limit, setLimit] = useState(10);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (keyword.trim()) {
      onSearch(keyword.trim(), searchType, limit);
    }
  };

  const exampleKeywords = [
    '深度学习在医疗影像的应用',
    '自然语言处理',
    '计算机视觉',
    '强化学习',
    '生成对抗网络',
    'Transformer架构'
  ];

  return (
    <div className="search-panel">
      <div className="search-intro">
        <h2>开始搜索</h2>
        <p>输入关键词，系统将从多个数据源搜索相关内容，包括学术论文、技术文章、产品信息、行业应用和前沿热点。</p>
      </div>

      <form onSubmit={handleSubmit} className="search-form">
        <div className="form-group">
          <label htmlFor="keyword">搜索关键词</label>
          <input
            id="keyword"
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="例如：深度学习在医疗影像的应用"
            className="search-input"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="searchType">搜索范围</label>
          <select
            id="searchType"
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
            className="search-select"
            disabled={loading}
          >
            <option value="all">全部</option>
            <option value="paper">学术论文</option>
            <option value="tech">技术文章</option>
            <option value="product">产品应用</option>
            <option value="industry">行业案例</option>
            <option value="trend">前沿热点</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="limit">结果数量</label>
          <select
            id="limit"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="search-select"
            disabled={loading}
          >
            <option value="5">5条</option>
            <option value="10">10条</option>
            <option value="15">15条</option>
            <option value="20">20条</option>
          </select>
        </div>

        <button
          type="submit"
          className="search-button"
          disabled={loading || !keyword.trim()}
        >
          {loading ? '搜索中...' : '开始搜索'}
        </button>
      </form>

      <div className="example-keywords">
        <h3>示例关键词</h3>
        <div className="keyword-chips">
          {exampleKeywords.map((example, index) => (
            <button
              key={index}
              className="keyword-chip"
              onClick={() => setKeyword(example)}
              disabled={loading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      <div className="search-features">
        <h3>功能特点</h3>
        <div className="features-grid">
          <div className="feature-card">
            <span className="feature-icon">🔍</span>
            <h4>多源搜索</h4>
            <p>整合学术、技术、产品等多个数据源</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">🎯</span>
            <h4>精准匹配</h4>
            <p>智能相关度算法，准确率90%+</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">⚡</span>
            <h4>实时抓取</h4>
            <p>实时从网络获取最新资讯</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">🤖</span>
            <h4>AI生成</h4>
            <p>自动生成高质量教学案例</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SearchPanel;
