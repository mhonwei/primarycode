import React, { useState } from 'react';
import '../styles/CaseGenerator.css';

function CaseGenerator({ onGenerate, loading }) {
  const [params, setParams] = useState({
    keyword: '',
    caseType: 'problem',
    difficulty: 'intermediate',
    focus: 'theory',
    audience: 'undergraduate',
    wordLimit: 1000
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (params.keyword.trim()) {
      onGenerate(params);
    }
  };

  const handleChange = (field, value) => {
    setParams(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="case-generator">
      <div className="generator-header">
        <h2>生成教学案例</h2>
        <p>设置案例参数，系统将基于搜索结果自动生成高质量的教学案例</p>
      </div>

      <form onSubmit={handleSubmit} className="generator-form">
        <div className="form-section">
          <h3>基本信息</h3>

          <div className="form-group">
            <label htmlFor="keyword">案例关键词 *</label>
            <input
              id="keyword"
              type="text"
              value={params.keyword}
              onChange={(e) => handleChange('keyword', e.target.value)}
              placeholder="例如：深度学习在医疗影像的应用"
              required
              disabled={loading}
            />
            <small>这将成为案例的核心主题</small>
          </div>
        </div>

        <div className="form-section">
          <h3>案例类型</h3>

          <div className="radio-group">
            <label className={`radio-card ${params.caseType === 'problem' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="caseType"
                value="problem"
                checked={params.caseType === 'problem'}
                onChange={(e) => handleChange('caseType', e.target.value)}
                disabled={loading}
              />
              <div className="radio-content">
                <span className="radio-icon">❓</span>
                <strong>问题导向型</strong>
                <p>以问题为中心，引导学生分析和解决</p>
              </div>
            </label>

            <label className={`radio-card ${params.caseType === 'project' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="caseType"
                value="project"
                checked={params.caseType === 'project'}
                onChange={(e) => handleChange('caseType', e.target.value)}
                disabled={loading}
              />
              <div className="radio-content">
                <span className="radio-icon">🎯</span>
                <strong>项目驱动型</strong>
                <p>完整项目流程，从设计到实施</p>
              </div>
            </label>

            <label className={`radio-card ${params.caseType === 'discussion' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="caseType"
                value="discussion"
                checked={params.caseType === 'discussion'}
                onChange={(e) => handleChange('caseType', e.target.value)}
                disabled={loading}
              />
              <div className="radio-content">
                <span className="radio-icon">💬</span>
                <strong>讨论型</strong>
                <p>多角度讨论，培养批判性思维</p>
              </div>
            </label>
          </div>
        </div>

        <div className="form-section">
          <h3>难度等级</h3>

          <div className="radio-group horizontal">
            <label className={`radio-option ${params.difficulty === 'beginner' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="difficulty"
                value="beginner"
                checked={params.difficulty === 'beginner'}
                onChange={(e) => handleChange('difficulty', e.target.value)}
                disabled={loading}
              />
              <span>🟢 初级</span>
            </label>

            <label className={`radio-option ${params.difficulty === 'intermediate' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="difficulty"
                value="intermediate"
                checked={params.difficulty === 'intermediate'}
                onChange={(e) => handleChange('difficulty', e.target.value)}
                disabled={loading}
              />
              <span>🟡 中级</span>
            </label>

            <label className={`radio-option ${params.difficulty === 'advanced' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="difficulty"
                value="advanced"
                checked={params.difficulty === 'advanced'}
                onChange={(e) => handleChange('difficulty', e.target.value)}
                disabled={loading}
              />
              <span>🔴 高级</span>
            </label>
          </div>
        </div>

        <div className="form-section">
          <h3>内容侧重点</h3>

          <div className="radio-group horizontal">
            <label className={`radio-option ${params.focus === 'theory' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="focus"
                value="theory"
                checked={params.focus === 'theory'}
                onChange={(e) => handleChange('focus', e.target.value)}
                disabled={loading}
              />
              <span>📚 技术原理</span>
            </label>

            <label className={`radio-option ${params.focus === 'business' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="focus"
                value="business"
                checked={params.focus === 'business'}
                onChange={(e) => handleChange('focus', e.target.value)}
                disabled={loading}
              />
              <span>💼 商业模式</span>
            </label>

            <label className={`radio-option ${params.focus === 'social' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="focus"
                value="social"
                checked={params.focus === 'social'}
                onChange={(e) => handleChange('focus', e.target.value)}
                disabled={loading}
              />
              <span>🌍 社会影响</span>
            </label>

            <label className={`radio-option ${params.focus === 'ethics' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="focus"
                value="ethics"
                checked={params.focus === 'ethics'}
                onChange={(e) => handleChange('focus', e.target.value)}
                disabled={loading}
              />
              <span>⚖️ 伦理问题</span>
            </label>
          </div>
        </div>

        <div className="form-section">
          <h3>目标受众</h3>

          <div className="radio-group horizontal">
            <label className={`radio-option ${params.audience === 'undergraduate' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="audience"
                value="undergraduate"
                checked={params.audience === 'undergraduate'}
                onChange={(e) => handleChange('audience', e.target.value)}
                disabled={loading}
              />
              <span>🎓 本科生</span>
            </label>

            <label className={`radio-option ${params.audience === 'graduate' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="audience"
                value="graduate"
                checked={params.audience === 'graduate'}
                onChange={(e) => handleChange('audience', e.target.value)}
                disabled={loading}
              />
              <span>👨‍🎓 研究生</span>
            </label>

            <label className={`radio-option ${params.audience === 'professional' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="audience"
                value="professional"
                checked={params.audience === 'professional'}
                onChange={(e) => handleChange('audience', e.target.value)}
                disabled={loading}
              />
              <span>💼 从业人员</span>
            </label>
          </div>
        </div>

        <div className="form-section">
          <h3>字数限制</h3>

          <div className="form-group">
            <input
              type="range"
              min="500"
              max="3000"
              step="100"
              value={params.wordLimit}
              onChange={(e) => handleChange('wordLimit', Number(e.target.value))}
              disabled={loading}
            />
            <div className="range-value">{params.wordLimit} 字</div>
          </div>
        </div>

        <button
          type="submit"
          className="generate-button"
          disabled={loading || !params.keyword.trim()}
        >
          {loading ? '生成中...' : '生成案例'}
        </button>
      </form>

      <div className="generator-tips">
        <h4>💡 生成建议</h4>
        <ul>
          <li>关键词应该明确具体，能够准确反映案例主题</li>
          <li>根据学生的知识水平选择合适的难度等级</li>
          <li>不同的案例类型适合不同的教学场景</li>
          <li>可以多次生成并比较，选择最合适的案例</li>
        </ul>
      </div>
    </div>
  );
}

export default CaseGenerator;
