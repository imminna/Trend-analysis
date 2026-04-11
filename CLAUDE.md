# 社群媒體趨勢分析網頁 — 專案規格與計劃

## 專案簡介

個人用途的趨勢分析儀表板，從 Instagram 和 Threads 收集熱門話題，進行情感分析與視覺化展示。
採用 GitHub Actions + GitHub Pages 完全免費部署，Python 爬蟲定時執行並將結果存為 JSON，React 前端讀取靜態資料顯示。

---

## 需求規格（Spec）

| 項目 | 規格 |
|------|------|
| 用途 | 個人使用 |
| 資料來源 | Instagram + Threads（認證爬蟲，session cookie） |
| 分析功能 | 熱門話題排行、趨勢走勢圖、情感分析（中英）、關鍵字雲 |
| 話題範圍 | 自訂關鍵字追蹤 + 自動發現熱門話題 |
| 更新頻率 | 每 6 小時自動 + 手動觸發按鈕 |
| 前端框架 | React + Vite + TypeScript + Tailwind CSS |
| 後端 | Python（無獨立伺服器，透過 GitHub Actions 排程執行） |
| 資料儲存 | JSON 檔案（commit 到 repo `data/` 目錄） |
| 部署 | GitHub Pages（前端）+ GitHub Actions（爬蟲） |

---

## 系統架構

```
GitHub Actions (cron 每 6h + workflow_dispatch 手動)
  └── Python 爬蟲 + NLP 分析
        └── 輸出 JSON 資料 → git commit 到 data/ 目錄

GitHub Pages
  └── React 前端讀取 data/*.json 並視覺化
```

**設計原則**：完全免費、無需伺服器，Session cookie 存在 GitHub Secrets，
爬蟲結果自動 commit 回 repo，前端靜態讀取 JSON。

---

## 專案目錄結構

```
social-trend-analyzer/
├── .github/
│   └── workflows/
│       ├── crawl.yml          # 爬蟲排程（cron + workflow_dispatch）
│       └── deploy.yml         # GitHub Pages 部署
│
├── scripts/                   # Python 爬蟲與分析
│   ├── crawlers/
│   │   ├── base_crawler.py    # 基底類別（rate limiting、retry 邏輯）
│   │   ├── instagram_crawler.py
│   │   └── threads_crawler.py
│   ├── analyzers/
│   │   ├── sentiment_analyzer.py   # 中英文情感分析
│   │   ├── keyword_extractor.py    # jieba (ZH) + nltk (EN)
│   │   └── trend_calculator.py     # 熱度分數計算
│   ├── config/
│   │   ├── keywords.json      # 用戶自訂追蹤關鍵字（可直接編輯）
│   │   └── settings.py        # 全域設定（讀取環境變數）
│   ├── utils/
│   │   └── data_writer.py     # JSON 寫入工具
│   ├── main.py                # 主入口（支援 --dry-run / --keywords）
│   └── requirements.txt
│
├── data/                      # 由 Actions 自動 commit，前端讀取
│   ├── trending.json          # 當前熱門話題排行
│   ├── history.json           # 歷史趨勢（最近 30 天）
│   ├── keywords.json          # 關鍵字雲資料
│   ├── sentiment.json         # 情感分析結果
│   └── meta.json              # 最後更新時間、狀態
│
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header/        # 最後更新時間、篩選、觸發按鈕
│   │   │   ├── TrendingList/  # 熱門話題排行榜
│   │   │   ├── TrendChart/    # 趨勢折線圖（Recharts）
│   │   │   ├── SentimentDashboard/  # 情感圓餅圖 + 橫向比較
│   │   │   └── KeywordCloud/  # 關鍵字雲（react-d3-cloud）
│   │   ├── hooks/
│   │   │   └── useData.ts     # 統一資料抓取 hook（並行 fetch）
│   │   └── types/index.ts     # TypeScript 型別定義
│   └── package.json
│
└── CLAUDE.md                  # 本檔案
```

---

## Python 爬蟲設計

### Instagram 爬蟲（`scripts/crawlers/instagram_crawler.py`）
- **工具**：`instaloader`
- **認證**：從環境變數 `IG_SESSION_ID` 讀取 session cookie，不需要密碼
- **抓取**：指定 hashtag 的最新貼文（按讚數、留言數、時間戳）
- **限制**：IG 無公開 trending API，熱門話題目前需手動指定關鍵字

### Threads 爬蟲（`scripts/crawlers/threads_crawler.py`）
- **工具**：直接呼叫 Threads Graph API（`https://graph.threads.net/v1.0`）
- **認證**：從環境變數 `THREADS_TOKEN` 讀取 access token
- **降級**：無 token 時嘗試網頁解析（資料有限）

### Rate Limiting（`scripts/crawlers/base_crawler.py`）
- 每次請求隨機延遲 2–5 秒
- 每個 hashtag 最多抓 50 篇貼文
- 失敗時指數退避 retry（最多 3 次）

---

## NLP 分析設計

### 情感分析（`scripts/analyzers/sentiment_analyzer.py`）
```
中文：SnowNLP（score 0~1，>0.6 為正面）
英文：VADER（compound score，>0.05 正面，<-0.05 負面）
語言偵測：langdetect（自動判斷中/英/其他）
```

### 關鍵字提取（`scripts/analyzers/keyword_extractor.py`）
```
中文：jieba TF-IDF
英文：nltk tokenize + stopwords 過濾
輸出：top 60 關鍵字，value 正規化到 10~100（供字雲視覺化）
```

### 熱度分數公式（`scripts/analyzers/trend_calculator.py`）
```
raw_score = likes × 1.0 + comments × 2.0
trend_score = raw_score / (hours_elapsed + 2)^1.5   ← 時間衰減
```

---

## JSON 資料格式

### `data/trending.json`
```json
{
  "updated_at": "2026-04-11T12:00:00Z",
  "topics": [
    {
      "tag": "#AI",
      "count": 1523,
      "trend_score": 98.5,
      "total_likes": 45230,
      "total_comments": 3210,
      "change": "+100%",
      "rank": 1,
      "source": ["instagram", "threads"]
    }
  ]
}
```

### `data/history.json`
```json
{
  "dates": ["2026-04-01", "2026-04-02"],
  "topics": { "#AI": [120, 135] }
}
```

### `data/sentiment.json`
```json
{
  "updated_at": "...",
  "overall": { "positive": 52.3, "neutral": 31.8, "negative": 15.9 },
  "by_topic": { "#AI": { "positive": 61.2, "neutral": 28.5, "negative": 10.3 } }
}
```

### `data/keywords.json`
```json
{
  "updated_at": "...",
  "words": [{ "text": "人工智慧", "value": 100 }]
}
```

### `data/meta.json`
```json
{
  "updated_at": "...",
  "status": "ok",
  "error": ""
}
```

---

## GitHub Actions Workflows

### `crawl.yml` — 爬蟲排程
- **觸發**：`cron: '0 0,6,12,18 * * *'`（每 6 小時）+ `workflow_dispatch`（手動）
- **環境變數**：`IG_SESSION_ID`、`THREADS_TOKEN`（從 GitHub Secrets 讀取）
- **流程**：checkout → setup Python → pip install → `python scripts/main.py` → git commit & push `data/`

### `deploy.yml` — GitHub Pages 部署
- **觸發**：push 到 main（`frontend/**` 或 `data/**` 有異動時）
- **流程**：checkout → setup Node → npm ci → vite build → copy `data/` → deploy to Pages
- **注意**：build 時自動帶入 `VITE_BASE_PATH=/<repo-name>/`

---

## React 前端技術選型

| 功能 | 套件 |
|------|------|
| 趨勢折線圖 | `recharts` LineChart |
| 情感圓餅/長條圖 | `recharts` PieChart / BarChart |
| 關鍵字雲 | `react-d3-cloud`（搭配 `--legacy-peer-deps`） |
| 圖示 | `lucide-react` |
| 樣式 | `tailwindcss` + `@tailwindcss/vite` |
| 資料抓取 | `fetch` + `Promise.all`（並行）|
| 手動觸發爬蟲 | GitHub Actions API `workflow_dispatch` |

### 手動觸發爬蟲按鈕
需在 GitHub Secrets 設定（或 `.env.local`）：
- `VITE_GH_OWNER` = GitHub 帳號
- `VITE_GH_REPO` = repo 名稱
- `VITE_GH_TOKEN` = 有 `actions:write` 權限的 PAT

---

## 部署步驟

1. **設定 GitHub Secrets**（Settings → Secrets → Actions）：
   - `IG_SESSION_ID`：瀏覽器 DevTools → Cookies → Instagram `sessionid`
   - `THREADS_TOKEN`：Threads access token（可選）
   - `VITE_GH_OWNER`、`VITE_GH_REPO`、`VITE_GH_TOKEN`（手動觸發用）

2. **啟用 GitHub Pages**：Settings → Pages → Source → **GitHub Actions**

3. **首次部署**：Actions → Deploy to GitHub Pages → Run workflow

4. **網址**：`https://hcvibe.github.io/Trend-analysis/`

---

## 本地開發

```bash
# 前端開發（使用 data/ 假資料）
cd frontend
npm install --legacy-peer-deps
npm run dev

# Python 爬蟲測試（不寫檔，只輸出 JSON）
cd scripts
pip install -r requirements.txt
python main.py --dry-run

# 指定額外關鍵字
python main.py --keywords "咖啡,穿搭"
```

---

## 重要注意事項

1. **爬蟲合規性**：IG/Threads ToS 禁止未授權爬蟲，個人小規模使用風險較低，但需控制頻率。
2. **Cookie 有效期**：Session cookie 約 30–90 天後過期，需定期更新 GitHub Secrets。
3. **資料量控制**：`history.json` 只保留最近 30 天，避免 repo 膨脹。
4. **Fallback 機制**：爬蟲失敗時保留上次成功的 JSON，`meta.json` 記錄錯誤狀態，前端顯示警告橫幅。
5. **`react-d3-cloud` 相容性**：需 `--legacy-peer-deps` 安裝，因其 peerDep 尚未更新支援 React 19。
