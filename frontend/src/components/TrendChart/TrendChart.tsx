import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity } from 'lucide-react';
import type { HistoryData } from '../../types';

interface TrendChartProps {
  history: HistoryData;
  selectedTag: string | null;
}

const COLORS = ['#818cf8', '#f472b6', '#34d399', '#fb923c', '#a78bfa', '#60a5fa', '#fbbf24', '#f87171'];

// 日期格式縮短為 MM/DD
function shortDate(d: string) {
  const parts = d.split('-');
  return `${parts[1]}/${parts[2]}`;
}

export default function TrendChart({ history, selectedTag }: TrendChartProps) {
  const allTags = Object.keys(history.topics);
  // 若有選中的話題只顯示該話題，否則顯示前 5 個
  const visibleTags = selectedTag && history.topics[selectedTag]
    ? [selectedTag]
    : allTags.slice(0, 5);

  // 轉換為 recharts 格式
  const chartData = history.dates.map((date, i) => {
    const row: Record<string, string | number> = { date: shortDate(date) };
    visibleTags.forEach(tag => {
      row[tag] = history.topics[tag]?.[i] ?? 0;
    });
    return row;
  });

  return (
    <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-4">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={16} className="text-indigo-400" />
        <h2 className="text-sm font-semibold text-slate-200">趨勢走勢（近 30 天）</h2>
        {selectedTag && (
          <span className="ml-auto text-xs text-indigo-300 bg-indigo-900/40 px-2 py-0.5 rounded">
            {selectedTag}
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: '#1e2130', border: '1px solid #334155', borderRadius: 8 }}
            labelStyle={{ color: '#94a3b8' }}
            itemStyle={{ color: '#e2e8f0' }}
          />
          <Legend
            wrapperStyle={{ fontSize: 12, color: '#94a3b8', paddingTop: 8 }}
          />
          {visibleTags.map((tag, i) => (
            <Line
              key={tag}
              type="monotone"
              dataKey={tag}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={selectedTag ? 2.5 : 1.5}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
