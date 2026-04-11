import { TrendingUp, Heart, MessageCircle } from 'lucide-react';
import type { Topic, PlatformFilter } from '../../types';

interface TrendingListProps {
  topics: Topic[];
  selectedTag: string | null;
  platformFilter: PlatformFilter;
  onSelectTag: (tag: string) => void;
}

const PLATFORM_COLORS: Record<string, string> = {
  instagram: 'bg-pink-500/20 text-pink-300',
  threads: 'bg-purple-500/20 text-purple-300',
};

function filterByPlatform(topics: Topic[], filter: PlatformFilter) {
  if (filter === 'all') return topics;
  return topics.filter(t => t.source.includes(filter));
}

export default function TrendingList({ topics, selectedTag, platformFilter, onSelectTag }: TrendingListProps) {
  const filtered = filterByPlatform(topics, platformFilter);

  return (
    <div className="bg-slate-800/60 rounded-xl border border-slate-700 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700">
        <TrendingUp size={16} className="text-indigo-400" />
        <h2 className="text-sm font-semibold text-slate-200">熱門話題排行</h2>
        <span className="ml-auto text-xs text-slate-500">{filtered.length} 個話題</span>
      </div>
      <ul className="divide-y divide-slate-700/50">
        {filtered.map((topic, i) => (
          <li
            key={topic.tag}
            onClick={() => onSelectTag(topic.tag)}
            className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-slate-700/40 ${
              selectedTag === topic.tag ? 'bg-indigo-900/30 border-l-2 border-indigo-500' : ''
            }`}
          >
            {/* 排名 */}
            <span className={`w-6 text-center text-sm font-bold flex-shrink-0 ${
              i === 0 ? 'text-yellow-400' : i === 1 ? 'text-slate-300' : i === 2 ? 'text-amber-600' : 'text-slate-500'
            }`}>
              {i + 1}
            </span>

            {/* 話題資訊 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white truncate">{topic.tag}</span>
                <span className="text-xs font-medium text-green-400 flex-shrink-0">{topic.change}</span>
              </div>
              <div className="flex items-center gap-3 mt-0.5">
                <span className="flex items-center gap-0.5 text-xs text-slate-400">
                  <Heart size={10} /> {topic.total_likes.toLocaleString()}
                </span>
                <span className="flex items-center gap-0.5 text-xs text-slate-400">
                  <MessageCircle size={10} /> {topic.total_comments.toLocaleString()}
                </span>
              </div>
            </div>

            {/* 平台標籤 */}
            <div className="flex gap-1 flex-shrink-0">
              {topic.source.map(p => (
                <span key={p} className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${PLATFORM_COLORS[p] || 'bg-slate-600 text-slate-300'}`}>
                  {p === 'instagram' ? 'IG' : 'TH'}
                </span>
              ))}
            </div>
          </li>
        ))}
        {filtered.length === 0 && (
          <li className="px-4 py-8 text-center text-slate-500 text-sm">
            該平台暫無資料
          </li>
        )}
      </ul>
    </div>
  );
}
