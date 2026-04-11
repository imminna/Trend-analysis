import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';
import { Smile } from 'lucide-react';
import type { SentimentData } from '../../types';

interface SentimentDashboardProps {
  sentiment: SentimentData;
  selectedTag: string | null;
}

const SENTIMENT_COLORS = {
  positive: '#34d399',
  neutral: '#94a3b8',
  negative: '#f87171',
};
const SENTIMENT_LABELS = {
  positive: '正面',
  neutral: '中性',
  negative: '負面',
};

export default function SentimentDashboard({ sentiment, selectedTag }: SentimentDashboardProps) {
  const current = selectedTag && sentiment.by_topic[selectedTag]
    ? sentiment.by_topic[selectedTag]
    : sentiment.overall;

  const title = selectedTag ? `${selectedTag} 情感分佈` : '整體情感分佈';

  const pieData = (Object.keys(SENTIMENT_COLORS) as Array<keyof typeof SENTIMENT_COLORS>).map(key => ({
    name: SENTIMENT_LABELS[key],
    value: current[key],
    fill: SENTIMENT_COLORS[key],
  }));

  // 各話題橫向比較 bar chart
  const barData = Object.entries(sentiment.by_topic).slice(0, 6).map(([tag, s]) => ({
    tag,
    正面: s.positive,
    中性: s.neutral,
    負面: s.negative,
  }));

  return (
    <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-4">
      <div className="flex items-center gap-2 mb-4">
        <Smile size={16} className="text-indigo-400" />
        <h2 className="text-sm font-semibold text-slate-200">情感分析</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 圓餅圖 */}
        <div>
          <p className="text-xs text-slate-400 mb-2 text-center">{title}</p>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={75}
                dataKey="value"
                paddingAngle={3}
              >
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1e2130', border: '1px solid #334155', borderRadius: 8 }}
                formatter={(val) => [`${val}%`]}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* 圖例 */}
          <div className="flex justify-center gap-4 mt-2">
            {pieData.map(d => (
              <div key={d.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: d.fill }} />
                <span className="text-xs text-slate-400">{d.name} {d.value}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* 各話題比較 */}
        <div>
          <p className="text-xs text-slate-400 mb-2 text-center">各話題情感比較</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} layout="vertical" margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} tickLine={false} domain={[0, 100]} />
              <YAxis type="category" dataKey="tag" tick={{ fill: '#94a3b8', fontSize: 10 }} tickLine={false} width={50} />
              <Tooltip
                contentStyle={{ background: '#1e2130', border: '1px solid #334155', borderRadius: 8 }}
                formatter={(val) => [`${val}%`]}
              />
              <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
              <Bar dataKey="正面" stackId="a" fill="#34d399" />
              <Bar dataKey="中性" stackId="a" fill="#94a3b8" />
              <Bar dataKey="負面" stackId="a" fill="#f87171" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
