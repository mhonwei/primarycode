import React, { useState } from 'react';
import axios from 'axios';
import './styles/App.css';
import SearchPanel from './components/SearchPanel';
import ResultsPanel from './components/ResultsPanel';
import CaseGenerator from './components/CaseGenerator';
import CaseViewer from './components/CaseViewer';

function App() {
  const [searchResults, setSearchResults] = useState(null);
  const [generatedCase, setGeneratedCase] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('search'); // search, results, generate, view

  const handleSearch = async (keyword, searchType, limit) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/search', {
        keyword,
        search_type: searchType,
        limit
      });

      setSearchResults(response.data.results);
      setActiveTab('results');
    } catch (err) {
      setError(err.response?.data?.error || '搜索失败，请重试');
      console.error('搜索错误:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCase = async (params) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/generate-case', {
        keyword: params.keyword,
        source_data: searchResults,
        case_type: params.caseType,
        difficulty: params.difficulty,
        focus: params.focus,
        audience: params.audience,
        word_limit: params.wordLimit
      });

      setGeneratedCase(response.data.case);
      setActiveTab('view');
    } catch (err) {
      setError(err.response?.data?.error || '案例生成失败，请重试');
      console.error('生成错误:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCase = async (format) => {
    try {
      const response = await axios.post('/api/export-case', {
        case: generatedCase,
        format
      });

      // 创建下载链接
      const content = response.data.content;
      const blob = new Blob([content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `case_${Date.now()}.${format === 'markdown' ? 'md' : format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('导出失败，请重试');
      console.error('导出错误:', err);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>AI案例智库系统</h1>
          <p className="subtitle">自动生成人工智能通识课程教学案例</p>
        </div>
        <nav className="nav-tabs">
          <button
            className={activeTab === 'search' ? 'active' : ''}
            onClick={() => setActiveTab('search')}
          >
            搜索
          </button>
          <button
            className={activeTab === 'results' ? 'active' : ''}
            onClick={() => setActiveTab('results')}
            disabled={!searchResults}
          >
            搜索结果
          </button>
          <button
            className={activeTab === 'generate' ? 'active' : ''}
            onClick={() => setActiveTab('generate')}
            disabled={!searchResults}
          >
            生成案例
          </button>
          <button
            className={activeTab === 'view' ? 'active' : ''}
            onClick={() => setActiveTab('view')}
            disabled={!generatedCase}
          >
            查看案例
          </button>
        </nav>
      </header>

      <main className="App-main">
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>处理中，请稍候...</p>
          </div>
        )}

        <div className="content-area">
          {activeTab === 'search' && (
            <SearchPanel onSearch={handleSearch} loading={loading} />
          )}

          {activeTab === 'results' && searchResults && (
            <ResultsPanel
              results={searchResults}
              onGenerateCase={() => setActiveTab('generate')}
            />
          )}

          {activeTab === 'generate' && searchResults && (
            <CaseGenerator
              onGenerate={handleGenerateCase}
              loading={loading}
            />
          )}

          {activeTab === 'view' && generatedCase && (
            <CaseViewer
              caseData={generatedCase}
              onExport={handleExportCase}
            />
          )}
        </div>
      </main>

      <footer className="App-footer">
        <p>© 2024 AI案例智库系统 | 准确度目标: 90%+ | 基于Flask + React构建</p>
      </footer>
    </div>
  );
}

export default App;
