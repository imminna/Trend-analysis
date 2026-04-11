import { useState, useCallback } from 'react';
import { useData } from './hooks/useData';
import Header from './components/Header/Header';
import TrendingList from './components/TrendingList/TrendingList';
import TrendChart from './components/TrendChart/TrendChart';
import SentimentDashboard from './components/SentimentDashboard/SentimentDashboard';
import KeywordCloud from './components/KeywordCloud/KeywordCloud';
import type { PlatformFilter } from './types';
import './index.css';

// GitHub Actions 手動觸發所需的設定（部署時設定環境變數）
const GH_OWNER = import.meta.env.VITE_GH_OWNER || '';
const GH_REPO = import.meta.env.VITE_GH_REPO || '';
const GH_TOKEN = import.meta.env.VITE_GH_TOKEN || '';
const WORKFLOW_ID = 'crawl.yml';

async function triggerGitHubActions(): Promise<boolean> {
  if (!GH_OWNER || !GH_REPO || !GH_TOKEN) {
    alert('尚未設定 GitHub Actions 觸發設定（VITE_GH_OWNER / VITE_GH_REPO / VITE_GH_TOKEN）');
    return false;
  }
  const res = await fetch(
    `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/workflows/${WORKFLOW_ID}/dispatches`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${GH_TOKEN}`,
        'Content-Type': 'application/json',
        Accept: 'application/vnd.github+json',
      },
      body: JSON.stringify({ ref: 'main' }),
    }
  );
  return res.status === 204;
}

export default function App() {
  const { trending, history, sentiment, keywords, meta, loading, error, refresh } = useData();
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [platformFilter, setPlatformFilter] = useState<PlatformFilter>('all');
  const [crawlTriggering, setCrawlTriggering] = useState(false);

  const handleTriggerCrawl = useCallback(async () => {
    setCrawlTriggering(true);
    try {
      const ok = await triggerGitHubActions();
      if (ok) {
        alert('爬蟲任務已觸發！GitHub Actions 通常需要 2-5 分鐘完成，請稍後手動重新載入。');
      } else {
        alert('觸發失敗，請確認 GH Token 權限設定。');
      }
    } catch {
      alert('網路錯誤，請稍後再試。');
    } finally {
      setCrawlTriggering(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-900">
      <Header
        meta={meta}
        loading={loading}
        platformFilter={platformFilter}
        onFilterChange={setPlatformFilter}
        onRefresh={refresh}
        onTriggerCrawl={handleTriggerCrawl}
        crawlTriggering={crawlTriggering}
      />

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-5">
        {/* 載入中 */}
        {loading && (
          <div className="flex items-center justify-center py-20 text-slate-400">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500 mr-3" />
            載入資料中…
          </div>
        )}

        {/* 錯誤 */}
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 text-red-300 text-sm">
            資料載入失敗：{error}
          </div>
        )}

        {/* 主要內容 */}
        {!loading && !error && trending && history && sentiment && keywords && (
          <>
            {/* 上方：排行榜 + 走勢圖 */}
            <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-5">
              <TrendingList
                topics={trending.topics}
                selectedTag={selectedTag}
                platformFilter={platformFilter}
                onSelectTag={tag => setSelectedTag(prev => prev === tag ? null : tag)}
              />
              <TrendChart
                history={history}
                selectedTag={selectedTag}
              />
            </div>

            {/* 情感分析 */}
            <SentimentDashboard
              sentiment={sentiment}
              selectedTag={selectedTag}
            />

            {/* 關鍵字雲 */}
            <KeywordCloud words={keywords.words} />
          </>
        )}
      </main>
    </div>
  );
}
