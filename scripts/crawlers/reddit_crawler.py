"""
reddit_crawler.py — Reddit 公開 API 爬蟲
使用 Reddit 不需認證的公開 JSON endpoint，抓取科技相關貼文。
"""
import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict
from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

# 科技 / AI 相關 subreddit（依話題相關性排序）
TECH_SUBREDDITS = [
    "ChatGPT", "artificial", "MachineLearning",
    "singularity", "technology", "programming",
]

# Reddit 公開 API：不需 token，但 User-Agent 必須有意義，否則會被 429
REDDIT_HEADERS = {
    "User-Agent": "SocialTrendAnalyzer/1.0 (personal research; open source)",
    "Accept": "application/json",
}


class RedditCrawler(BaseCrawler):
    """Reddit 公開 API 爬蟲，不需要任何認證"""

    def __init__(self):
        super().__init__("reddit")
        self.session = requests.Session()
        self.session.headers.update(REDDIT_HEADERS)
        logger.info("[Reddit] 初始化完成（公開模式，不需認證）")

    # ──────────────────────────────────────────────
    # 公開介面
    # ──────────────────────────────────────────────

    def fetch_hashtag_posts(self, hashtag: str, max_posts: int = 25) -> List[Dict]:
        """搜尋 Reddit 過去一週含有此關鍵字的熱門貼文"""
        keyword = hashtag.lstrip("#")
        posts = []
        try:
            def _fetch():
                resp = self.session.get(
                    "https://www.reddit.com/search.json",
                    params={
                        "q": keyword,
                        "sort": "hot",
                        "t": "week",
                        "limit": min(max_posts, 25),
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                children = resp.json().get("data", {}).get("children", [])
                for child in children:
                    post = self._parse_post(child.get("data", {}), hashtag)
                    if post:
                        posts.append(post)
                        self._rate_limit()
                return posts

            return self._retry(_fetch)
        except Exception as e:
            logger.warning(f"[Reddit] #{keyword} 搜尋失敗: {e}")
            return []

    def fetch_trending(self) -> List[str]:
        """從科技 subreddit 的熱門貼文標題中萃取趨勢關鍵字"""
        trending = set()
        try:
            for sub in TECH_SUBREDDITS[:3]:
                self._rate_limit()
                resp = self.session.get(
                    f"https://www.reddit.com/r/{sub}/hot.json",
                    params={"limit": 10},
                    timeout=15,
                )
                if resp.status_code != 200:
                    continue
                children = resp.json().get("data", {}).get("children", [])
                for child in children:
                    title = child.get("data", {}).get("title", "")
                    # 取長度 > 4 的英文詞作為候選關鍵字
                    words = [w for w in title.split() if len(w) > 4 and w.isalpha()]
                    trending.update(words[:3])
        except Exception as e:
            logger.info(f"[Reddit] 熱門話題取得失敗（使用自訂關鍵字）: {e}")
        return list(trending)[:20]

    # ──────────────────────────────────────────────
    # 內部解析
    # ──────────────────────────────────────────────

    def _parse_post(self, data: Dict, hashtag: str) -> Dict | None:
        """將 Reddit API 回傳的貼文物件轉換為統一格式"""
        try:
            title = data.get("title", "")
            body = data.get("selftext", "")[:300]
            text = f"{title} {body}".strip()

            created = data.get("created_utc", 0)
            ts = datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else ""

            permalink = data.get("permalink", "")
            return {
                "id": data.get("id", ""),
                "platform": "reddit",
                "hashtag": hashtag,
                "text": text,
                "likes": int(data.get("ups", 0)),
                "comments": int(data.get("num_comments", 0)),
                "timestamp": ts,
                "url": f"https://reddit.com{permalink}",
            }
        except Exception as e:
            logger.debug(f"[Reddit] 解析貼文失敗: {e}")
            return None
