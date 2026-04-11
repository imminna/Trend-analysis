import { RefreshCw, BarChart2, AlertTriangle } from 'lucide-react';
import type { MetaData, PlatformFilter } from '../../types';

interface HeaderProps {
  meta: MetaData | null;
  loading: boolean;
  platformFilter: PlatformFilter;
  onFilterChange: (filter: PlatformFilter) => void;
  onRefresh: () => void;
  onTriggerCrawl: () => void;
  crawlTriggering: boolean;
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString('zh-TW', {
      timeZone: 'Asia/Taipei',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

const FILTERS: { value: PlatformFilter; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'threads', label: 'Threads' },
];

export default function Header({
  meta, loading, platformFilter, onFilterChange, onRefresh, onTriggerCrawl, crawlTriggering
}: HeaderProps) {
  return (
    <header className="border-b border-slate-700 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center gap-3">
        {/* 標題 */}
        <div className="flex items-center gap-2 mr-auto">
          <BarChart2 className="text-pink-500" size={22} />
          <h1 className="text-lg font-bold text-white tracking-tight">
            社群趨勢分析
          </h1>
        </div>

        {/* 狀態警告 */}
        {meta?.status === 'error' && (
          <div className="flex items-center gap-1 text-amber-400 text-xs bg-amber-900/30 px-2 py-1 rounded">
            <AlertTriangle size={14} />
            <span>上次爬蟲失敗</span>
          </div>
        )}

        {/* 最後更新時間 */}
        {meta?.updated_at && (
          <span className="text-slate-400 text-xs hidden sm:block">
            更新於 {formatDate(meta.updated_at)}
          </span>
        )}

        {/* 平台篩選 */}
        <div className="flex bg-slate-800 rounded-lg p-0.5 gap-0.5">
          {FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => onFilterChange(f.value)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                platformFilter === f.value
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* 重新載入資料 */}
        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded-lg transition-colors disabled:opacity-50"
          title="重新載入 JSON 資料"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          重新載入
        </button>

        {/* 觸發新一輪爬蟲 */}
        <button
          onClick={onTriggerCrawl}
          disabled={crawlTriggering}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-700 hover:bg-indigo-600 text-white text-xs rounded-lg transition-colors disabled:opacity-50 font-medium"
          title="觸發 GitHub Actions 爬蟲（需設定 GH Token）"
        >
          {crawlTriggering ? '觸發中…' : '立即爬取'}
        </button>
      </div>
    </header>
  );
}
