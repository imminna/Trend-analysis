import { useState, useEffect, useCallback } from 'react';
import type { TrendingData, HistoryData, SentimentData, KeywordsData, MetaData } from '../types';

// 在 GitHub Pages 環境下，data/ 目錄與前端同 repo，直接相對路徑即可
const DATA_BASE = import.meta.env.BASE_URL.replace(/\/$/, '');

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${DATA_BASE}/${path}?t=${Date.now()}`);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.json();
}

export interface AppData {
  trending: TrendingData | null;
  history: HistoryData | null;
  sentiment: SentimentData | null;
  keywords: KeywordsData | null;
  meta: MetaData | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useData(): AppData {
  const [trending, setTrending] = useState<TrendingData | null>(null);
  const [history, setHistory] = useState<HistoryData | null>(null);
  const [sentiment, setSentiment] = useState<SentimentData | null>(null);
  const [keywords, setKeywords] = useState<KeywordsData | null>(null);
  const [meta, setMeta] = useState<MetaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [t, h, s, k, m] = await Promise.all([
        fetchJSON<TrendingData>('data/trending.json'),
        fetchJSON<HistoryData>('data/history.json'),
        fetchJSON<SentimentData>('data/sentiment.json'),
        fetchJSON<KeywordsData>('data/keywords.json'),
        fetchJSON<MetaData>('data/meta.json'),
      ]);
      setTrending(t);
      setHistory(h);
      setSentiment(s);
      setKeywords(k);
      setMeta(m);
    } catch (e) {
      setError(e instanceof Error ? e.message : '資料載入失敗');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return { trending, history, sentiment, keywords, meta, loading, error, refresh: load };
}
