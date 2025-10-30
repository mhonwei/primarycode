import React, { useState } from 'react';
import '../styles/ResultsPanel.css';

function ResultsPanel({ results, onGenerateCase }) {
  const [activeCategory, setActiveCategory] = useState('all');

  const categories = [
    { key: 'all', label: '全部', icon: '📚' },
    { key: 'papers', label: '学术论文', icon: '📄' },
    { key: 'tech', label: '技术文章', icon: '💻' },
    { key: 'products', label: '产品应用', icon: '🚀' },
    { key: 'industry', label: '行业案例', icon: '🏢' },
    { key: 'trends', label: '前沿热点', icon: '🔥' }
  ];

  const getTotalCount = () => {
    return Object.values(results).reduce((sum, items) => sum + (items?.length || 0), 0);
  };

  const renderPapers = (papers) => (
    <div className="results-section">
      <h3>📄 学术论文 ({papers.length})</h3>
      <div className="results-grid">
        {papers.map((paper, index) => (
          <div key={index} className="result-card paper-card">
            <div className="card-header">
              <h4>{paper.title}</h4>
              <span className="relevance-badge">{paper.relevance_score}%</span>
            </div>
            <p className="authors">作者: {paper.authors.join(', ')}</p>
            <p className="summary">{paper.summary.substring(0, 200)}...</p>
            <div className="card-meta">
              <span className="date">📅 {paper.published}</span>
              <a href={paper.link} target="_blank" rel="noopener noreferrer" className="link-button">
                查看论文 →
              </a>
            </div>
            {paper.categories && paper.categories.length > 0 && (
              <div className="tags">
                {paper.categories.slice(0, 3).map((cat, i) => (
                  <span key={i} className="tag">{cat}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderTech = (tech) => (
    <div className="results-section">
      <h3>💻 技术文章 ({tech.length})</h3>
      <div className="results-grid">
        {tech.map((item, index) => (
          <div key={index} className="result-card tech-card">
            <div className="card-header">
              <h4>{item.title}</h4>
              <span className="relevance-badge">{item.relevance_score}%</span>
            </div>
            <p className="description">{item.description}</p>
            <div className="card-meta">
              <span className="language">
                <span className="icon">🔧</span> {item.language}
              </span>
              <span className="stars">
                <span className="icon">⭐</span> {item.stars.toLocaleString()}
              </span>
            </div>
            <div className="tags">
              {item.topics && item.topics.slice(0, 3).map((topic, i) => (
                <span key={i} className="tag">{topic}</span>
              ))}
            </div>
            <a href={item.url} target="_blank" rel="noopener noreferrer" className="link-button">
              访问项目 →
            </a>
          </div>
        ))}
      </div>
    </div>
  );

  const renderProducts = (products) => (
    <div className="results-section">
      <h3>🚀 产品应用 ({products.length})</h3>
      <div className="results-grid">
        {products.map((product, index) => (
          <div key={index} className="result-card product-card">
            <div className="card-header">
              <h4>{product.name}</h4>
              <span className="relevance-badge">{product.relevance_score}%</span>
            </div>
            <p className="category">{product.category}</p>
            <p className="description">{product.description}</p>
            <div className="product-stats">
              <span>⭐ {product.rating}</span>
              <span>👥 {product.users.toLocaleString()} 用户</span>
              <span>💰 {product.pricing}</span>
            </div>
            <div className="features">
              <strong>核心功能:</strong>
              <ul>
                {product.features.slice(0, 3).map((feature, i) => (
                  <li key={i}>{feature}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderIndustry = (industry) => (
    <div className="results-section">
      <h3>🏢 行业案例 ({industry.length})</h3>
      <div className="results-grid">
        {industry.map((app, index) => (
          <div key={index} className="result-card industry-card">
            <div className="card-header">
              <h4>{app.title}</h4>
              <span className="relevance-badge">{app.relevance_score}%</span>
            </div>
            <div className="industry-meta">
              <span className="industry-tag">{app.industry}</span>
              <span className="company">{app.company}</span>
            </div>
            <p className="description">{app.description}</p>
            <div className="benefits">
              <strong>成效:</strong>
              <ul>
                {app.benefits.slice(0, 2).map((benefit, i) => (
                  <li key={i}>{benefit}</li>
                ))}
              </ul>
            </div>
            <div className="card-footer">
              <span className="impact">影响力: {app.impact_score}%</span>
              <span className="date">📅 {app.published_date}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderTrends = (trends) => (
    <div className="results-section">
      <h3>🔥 前沿热点 ({trends.length})</h3>
      <div className="results-grid">
        {trends.map((trend, index) => (
          <div key={index} className="result-card trend-card">
            <div className="card-header">
              <h4>{trend.title}</h4>
              <span className="hotness-badge">🔥 {Math.round(trend.hotness_score)}</span>
            </div>
            <span className="trend-type">{trend.type}</span>
            <p className="summary">{trend.summary}</p>
            <div className="trend-stats">
              <span>👁️ {trend.views.toLocaleString()}</span>
              <span>💬 {trend.comments.toLocaleString()}</span>
              <span>🔄 {trend.shares.toLocaleString()}</span>
            </div>
            <div className="tags">
              {trend.tags && trend.tags.map((tag, i) => (
                <span key={i} className="tag">{tag}</span>
              ))}
            </div>
            <div className="card-footer">
              <span className="author">✍️ {trend.author}</span>
              <span className="date">📅 {trend.published_date}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="results-panel">
      <div className="results-header">
        <h2>搜索结果</h2>
        <p>找到 <strong>{getTotalCount()}</strong> 条相关内容</p>
      </div>

      <div className="category-tabs">
        {categories.map(cat => {
          const count = cat.key === 'all'
            ? getTotalCount()
            : results[cat.key]?.length || 0;

          return (
            <button
              key={cat.key}
              className={`category-tab ${activeCategory === cat.key ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat.key)}
              disabled={count === 0 && cat.key !== 'all'}
            >
              <span className="tab-icon">{cat.icon}</span>
              <span className="tab-label">{cat.label}</span>
              <span className="tab-count">{count}</span>
            </button>
          );
        })}
      </div>

      <div className="results-content">
        {(activeCategory === 'all' || activeCategory === 'papers') && results.papers && results.papers.length > 0 && renderPapers(results.papers)}
        {(activeCategory === 'all' || activeCategory === 'tech') && results.tech && results.tech.length > 0 && renderTech(results.tech)}
        {(activeCategory === 'all' || activeCategory === 'products') && results.products && results.products.length > 0 && renderProducts(results.products)}
        {(activeCategory === 'all' || activeCategory === 'industry') && results.industry && results.industry.length > 0 && renderIndustry(results.industry)}
        {(activeCategory === 'all' || activeCategory === 'trends') && results.trends && results.trends.length > 0 && renderTrends(results.trends)}

        {getTotalCount() === 0 && (
          <div className="no-results">
            <p>没有找到相关结果，请尝试其他关键词</p>
          </div>
        )}
      </div>

      <div className="action-panel">
        <button className="generate-case-button" onClick={onGenerateCase}>
          基于这些结果生成教学案例 →
        </button>
      </div>
    </div>
  );
}

export default ResultsPanel;
