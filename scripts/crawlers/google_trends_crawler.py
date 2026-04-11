"""
google_trends_crawler.py — Google Trends 爬蟲
使用 pytrends 抓取關鍵字搜尋趨勢，完全不需要任何 token。
"""
import time
import logging
import warnings
from datetime import datetime, timezone
from typing import List, Dict
from pytrends.request import TrendReq
from .base_crawler import BaseCrawler

# pytrends 內部使用 pandas fillna，在新版 pandas 會產生 FutureWarning，抑制之
warnings.filterwarnings("ignore", category=FutureWarning, module="pytrends")

logger = logging.getLogger(__name__)

# Google Trends 比一般 API 更容易被 rate limit，每次請求至少間隔 5 秒
GT_REQUEST_DELAY = 5.0


class GoogleTrendsCrawler(BaseCrawler):
    """Google Trends 爬蟲，以台灣地區為主，抓取 7 天內關鍵字熱度"""

    def __init__(self):
        super().__init__("google_trends")
        # hl=zh-TW 語系、tz=480 台灣時區（UTC+8）
        # 不傳 retries/backoff_factor，避免與 urllib3 2.x 的 API 變更衝突
        self.pytrends = TrendReq(hl="zh-TW", tz=480, timeout=(10, 25))
        logger.info("[GoogleTrends] 初始化完成（台灣地區、7 天時間範圍）")

    # ──────────────────────────────────────────────
    # 公開介面
    # ──────────────────────────────────────────────

    def fetch_hashtag_posts(self, hashtag: str, max_posts: int = 10) -> List[Dict]:
        """
        將 Google Trends 的時間序列資料轉換為 post 格式。
        每個時間點 = 一筆「post」，熱度值 (0~100) 對應 likes。
        """
        keyword = hashtag.lstrip("#")
        posts = []
        try:
            time.sleep(GT_REQUEST_DELAY)
            self.pytrends.build_payload(
                [keyword],
                timeframe="now 7-d",
                geo="TW",
            )
            interest = self.pytrends.interest_over_time()

            if interest.empty or keyword not in interest.columns:
                logger.info(f"[GoogleTrends] #{keyword}: 無趨勢資料")
                return []

            # 取最近 max_posts 個時間點（每小時一筆）
            recent = interest[keyword].tail(max_posts)
            for ts, score in recent.items():
                score = int(score)
                if score == 0:
                    continue
                posts.append({
                    "id": f"gt_{keyword}_{ts.strftime('%Y%m%d%H')}",
                    "platform": "google_trends",
                    "hashtag": hashtag,
                    # text 留空，避免合成數字字串污染關鍵字提取
                    "text": "",
                    # 熱度 0~100 放大 100 倍，與社群平台的讚數量級對齊
                    "likes": score * 100,
                    "comments": 0,
                    "timestamp": ts.isoformat(),
                    "url": f"https://trends.google.com/trends/explore?q={keyword}&geo=TW",
                })

            logger.info(f"[GoogleTrends] #{keyword}: {len(posts)} 個時間點")
        except Exception as e:
            logger.warning(f"[GoogleTrends] #{keyword} 失敗: {e}")
        return posts

    def fetch_trending(self) -> List[str]:
        """取得 Google Trends 台灣即時熱搜關鍵字"""
        try:
            time.sleep(GT_REQUEST_DELAY)
            df = self.pytrends.trending_searches(pn="taiwan")
            keywords = df[0].tolist()[:20]
            logger.info(f"[GoogleTrends] 熱搜: {keywords[:5]}…")
            return keywords
        except Exception as e:
            logger.info(f"[GoogleTrends] 熱搜取得失敗（使用自訂關鍵字）: {e}")
            return []
