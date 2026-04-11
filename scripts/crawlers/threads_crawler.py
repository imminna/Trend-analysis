import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict
from .base_crawler import BaseCrawler
from config.settings import THREADS_TOKEN

logger = logging.getLogger(__name__)

# Threads 非官方 API 端點（基於逆向工程，可能隨時失效）
THREADS_API_BASE = "https://www.threads.net/api/v1"
THREADS_GRAPH_API = "https://graph.threads.net/v1.0"


class ThreadsCrawler(BaseCrawler):
    """Threads 爬蟲，優先使用官方 Graph API，降級到非官方端點"""

    def __init__(self):
        super().__init__("threads")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        if THREADS_TOKEN:
            self.session.headers["Authorization"] = f"Bearer {THREADS_TOKEN}"

    def fetch_hashtag_posts(self, hashtag: str, max_posts: int = 50) -> List[Dict]:
        """抓取指定 hashtag 的 Threads 貼文"""
        tag = hashtag.lstrip("#")
        posts = []

        if THREADS_TOKEN:
            posts = self._fetch_via_graph_api(tag, max_posts)
        else:
            posts = self._fetch_via_scrape(tag, max_posts)

        return posts

    def _fetch_via_graph_api(self, tag: str, max_posts: int) -> List[Dict]:
        """使用 Threads Graph API（需要 access token）"""
        posts = []
        try:
            url = f"{THREADS_GRAPH_API}/threads"
            params = {
                "q": f"#{tag}",
                "fields": "id,text,like_count,reply_count,timestamp,permalink",
                "limit": min(max_posts, 100),
                "access_token": THREADS_TOKEN,
            }

            def _fetch():
                resp = self.session.get(url, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("data", []):
                    posts.append({
                        "id": item.get("id"),
                        "platform": "threads",
                        "hashtag": f"#{tag}",
                        "text": item.get("text", ""),
                        "likes": item.get("like_count", 0),
                        "comments": item.get("reply_count", 0),
                        "timestamp": item.get("timestamp", ""),
                        "url": item.get("permalink", ""),
                    })
                    self._rate_limit()
                return posts

            return self._retry(_fetch)
        except Exception as e:
            logger.error(f"[Threads] Graph API 抓取 #{tag} 失敗: {e}")
            return []

    def _fetch_via_scrape(self, tag: str, max_posts: int) -> List[Dict]:
        """降級方案：直接解析 Threads 網頁（較不穩定）"""
        logger.warning(f"[Threads] 未設定 THREADS_TOKEN，改用網頁解析（資料有限）")
        posts = []
        try:
            url = f"https://www.threads.net/search?q=%23{tag}&serp_type=tags"
            resp = self.session.get(url, timeout=15)
            # 網頁返回 HTML，需要解析 __initialData__ JSON
            # 此處回傳空清單，實際部署時可加入 BeautifulSoup 解析
            logger.info(f"[Threads] 網頁解析 #{tag}，狀態碼: {resp.status_code}")
        except Exception as e:
            logger.error(f"[Threads] 網頁抓取 #{tag} 失敗: {e}")
        return posts

    def fetch_trending(self) -> List[str]:
        """取得 Threads 當前熱門話題"""
        if not THREADS_TOKEN:
            logger.warning("[Threads] 未設定 THREADS_TOKEN，無法取得熱門話題")
            return []
        try:
            url = f"{THREADS_GRAPH_API}/trending_topics"
            params = {"access_token": THREADS_TOKEN, "limit": 20}
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return [item.get("name", "") for item in data.get("data", [])]
        except Exception as e:
            logger.warning(f"[Threads] 取得熱門話題失敗: {e}")
        return []
