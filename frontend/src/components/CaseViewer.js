import React, { useState } from 'react';
import '../styles/CaseViewer.css';

function CaseViewer({ caseData, onExport }) {
  const [exportFormat, setExportFormat] = useState('markdown');

  const handleExport = () => {
    onExport(exportFormat);
  };

  const renderSection = (title, content, icon = '📝') => {
    if (!content) return null;

    return (
      <div className="case-section">
        <h3>
          <span className="section-icon">{icon}</span>
          {title}
        </h3>
        {typeof content === 'string' ? (
          <div className="section-content">{content}</div>
        ) : Array.isArray(content) ? (
          <ul className="section-list">
            {content.map((item, index) => (
              <li key={index}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
            ))}
          </ul>
        ) : typeof content === 'object' ? (
          <div className="section-content">
            {Object.entries(content).map(([key, value]) => (
              <div key={key} className="subsection">
                <strong>{key}:</strong>
                {typeof value === 'string' ? (
                  <p>{value}</p>
                ) : Array.isArray(value) ? (
                  <ul>
                    {value.map((item, i) => (
                      <li key={i}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
                    ))}
                  </ul>
                ) : (
                  <pre>{JSON.stringify(value, null, 2)}</pre>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="section-content">{String(content)}</div>
        )}
      </div>
    );
  };

  const renderProjectPhases = (phases) => {
    if (!phases) return null;

    return (
      <div className="case-section">
        <h3>
          <span className="section-icon">📅</span>
          项目阶段
        </h3>
        <div className="phases-timeline">
          {phases.map((phase, index) => (
            <div key={index} className="phase-card">
              <div className="phase-header">
                <h4>{phase.phase}</h4>
                <span className="phase-duration">{phase.duration}</span>
              </div>
              <div className="phase-content">
                <div className="phase-tasks">
                  <strong>任务:</strong>
                  <ul>
                    {phase.tasks.map((task, i) => (
                      <li key={i}>{task}</li>
                    ))}
                  </ul>
                </div>
                <div className="phase-deliverables">
                  <strong>交付物:</strong>
                  <ul>
                    {phase.deliverables.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderDiscussionScenarios = (scenarios) => {
    if (!scenarios) return null;

    return (
      <div className="case-section">
        <h3>
          <span className="section-icon">💭</span>
          讨论场景
        </h3>
        <div className="scenarios">
          {scenarios.map((scenario, index) => (
            <div key={index} className="scenario-card">
              <h4>{scenario.scenario}</h4>
              <p className="scenario-description">{scenario.description}</p>
              <div className="scenario-questions">
                <strong>讨论问题:</strong>
                <ol>
                  {scenario.questions.map((q, i) => (
                    <li key={i}>{q}</li>
                  ))}
                </ol>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderReferences = (references) => {
    if (!references || references.length === 0) return null;

    return (
      <div className="case-section">
        <h3>
          <span className="section-icon">📚</span>
          参考资料
        </h3>
        <div className="references">
          {references.map((ref, index) => (
            <div key={index} className="reference-item">
              <span className="ref-type">{ref.type}</span>
              <div className="ref-content">
                <strong>{ref.title}</strong>
                {ref.authors && <p className="ref-authors">{ref.authors}</p>}
                {ref.description && <p className="ref-description">{ref.description}</p>}
                {ref.link && (
                  <a href={ref.link} target="_blank" rel="noopener noreferrer">
                    查看详情 →
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="case-viewer">
      <div className="case-header">
        <div className="case-title-section">
          <h2>{caseData.title}</h2>
          <div className="case-meta">
            <span className="meta-badge">{caseData.case_type}</span>
            <span className="meta-badge">{caseData.difficulty_level}</span>
            <span className="meta-badge">{caseData.target_audience}</span>
            {caseData.metadata && (
              <span className="meta-info">
                预计阅读时间: {caseData.metadata.estimated_reading_time} 分钟
              </span>
            )}
          </div>
        </div>

        <div className="case-actions">
          <div className="export-section">
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              className="export-select"
            >
              <option value="markdown">Markdown</option>
              <option value="html">HTML</option>
              <option value="json">JSON</option>
            </select>
            <button onClick={handleExport} className="export-button">
              📥 导出案例
            </button>
          </div>
        </div>
      </div>

      <div className="case-content">
        {/* 问题导向型案例 */}
        {caseData.case_type === '问题导向型' && (
          <>
            {renderSection('背景介绍', caseData.background, '📖')}
            {renderSection('问题陈述', caseData.problem_statement, '❓')}
            {renderSection('学习目标', caseData.learning_objectives, '🎯')}
            {renderSection('技术基础', caseData.technical_foundation, '🔧')}
            {renderSection('案例分析', caseData.case_analysis, '🔍')}
            {renderSection('解决方案', caseData.solution_approach, '💡')}
            {renderSection('实施细节', caseData.implementation_details, '⚙️')}
            {renderSection('讨论问题', caseData.discussion_questions, '💬')}
            {renderReferences(caseData.further_reading)}
            {renderSection('评估标准', caseData.assessment, '📊')}
            {renderSection('教学建议', caseData.teaching_tips, '👨‍🏫')}
          </>
        )}

        {/* 项目驱动型案例 */}
        {caseData.case_type === '项目驱动型' && (
          <>
            {renderSection('项目概述', caseData.project_overview, '📋')}
            {renderSection('项目目标', caseData.project_objectives, '🎯')}
            {renderSection('先修知识', caseData.prerequisites, '📚')}
            {renderProjectPhases(caseData.project_phases)}
            {renderSection('技术栈', caseData.technical_stack, '🔧')}
            {renderSection('项目资源', caseData.resources, '📦')}
            {renderSection('评估标准', caseData.evaluation_criteria, '📊')}
            {renderSection('常见挑战', caseData.common_challenges, '⚠️')}
            {renderSection('教学建议', caseData.teaching_tips, '👨‍🏫')}
          </>
        )}

        {/* 讨论型案例 */}
        {caseData.case_type === '讨论型' && (
          <>
            {renderSection('案例概述', caseData.case_overview, '📋')}
            {renderSection('背景故事', caseData.background_story, '📖')}
            {renderSection('关键利益相关方', caseData.key_stakeholders, '👥')}
            {renderSection('核心议题', caseData.core_issues, '🎯')}
            {renderDiscussionScenarios(caseData.discussion_scenarios)}
            {renderSection('讨论框架', caseData.discussion_framework, '🗂️')}
            {renderSection('分析指南', caseData.case_analysis_guide, '🔍')}
            {renderReferences(caseData.recommended_readings)}
            {renderSection('评估标准', caseData.assessment_rubric, '📊')}
            {renderSection('教学建议', caseData.teaching_tips, '👨‍🏫')}
          </>
        )}
      </div>

      {caseData.metadata && (
        <div className="case-footer">
          <div className="metadata-info">
            <p>生成时间: {caseData.metadata.generated_at}</p>
            <p>关键词: {caseData.metadata.keyword}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default CaseViewer;
