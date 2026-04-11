export interface Topic {
  tag: string;
  count: number;
  trend_score: number;
  total_likes: number;
  total_comments: number;
  change: string;
  rank: number;
  source: string[];
}

export interface TrendingData {
  updated_at: string;
  topics: Topic[];
}

export interface HistoryData {
  dates: string[];
  topics: Record<string, number[]>;
}

export interface SentimentRatio {
  positive: number;
  neutral: number;
  negative: number;
}

export interface SentimentData {
  updated_at: string;
  overall: SentimentRatio;
  by_topic: Record<string, SentimentRatio>;
}

export interface KeywordWord {
  text: string;
  value: number;
}

export interface KeywordsData {
  updated_at: string;
  words: KeywordWord[];
}

export interface MetaData {
  updated_at: string;
  status: 'ok' | 'error';
  error: string;
}

export type PlatformFilter = 'all' | 'instagram' | 'threads';
