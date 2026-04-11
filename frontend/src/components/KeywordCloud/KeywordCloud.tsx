import ReactWordcloud from 'react-d3-cloud';
import { Tag } from 'lucide-react';
import type { KeywordWord } from '../../types';

interface KeywordCloudProps {
  words: KeywordWord[];
}

const COLORS = [
  '#818cf8', '#f472b6', '#34d399', '#fb923c',
  '#a78bfa', '#60a5fa', '#fbbf24', '#f87171',
  '#6ee7b7', '#93c5fd', '#c4b5fd', '#fca5a5',
];

export default function KeywordCloud({ words }: KeywordCloudProps) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d3Words: any[] = words.map(w => ({ text: w.text, value: w.value }));
  const maxVal = Math.max(...d3Words.map((w: { value: number }) => w.value), 1);

  return (
    <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-4">
      <div className="flex items-center gap-2 mb-4">
        <Tag size={16} className="text-indigo-400" />
        <h2 className="text-sm font-semibold text-slate-200">關鍵字雲</h2>
        <span className="ml-auto text-xs text-slate-500">{words.length} 個詞</span>
      </div>
      <div className="w-full overflow-hidden rounded-lg" style={{ height: 280 }}>
        <ReactWordcloud
          data={d3Words}
          width={800}
          height={260}
          font="system-ui, sans-serif"
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          fontSize={(word: any) => 14 + ((word.value ?? 1) / maxVal) * 38}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          rotate={(_: any, i: number) => (i % 3 === 0 ? 90 : i % 5 === 0 ? -90 : 0)}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          fill={(_d: any, i: number) => COLORS[i % COLORS.length]}
          padding={3}
        />
      </div>
    </div>
  );
}
