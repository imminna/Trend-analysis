import requests
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict
from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

# Threads 網頁版內部 API（不需要 token，模擬瀏覽器行為）
THREADS_SEARCH_URL = "https://www.threads.net/api/v1/search/hashtags/"
THREADS_GRAPHQL_URL = "https://www.threads.net/api/graphql"

# 模擬 Threads 網頁版的請求 headers
PUBLIC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "x-ig-app-id": "238260118697367",   # Threads web app ID（公開）
    "x-fb-lsd": "AVqbxe3J_YA",
    "Referer": "https://www.threads.net/",
    "Origin": "https://www.threads.net",
}


class ThreadsCrawler(BaseCrawler):
    """Threads 公開爬蟲，不需要 token，抓取公開 hashtag 貼文"""

    def __init__(self):
        super().__init__("threads")
        self.session = requests.Session()
        self.session.headers.update(PUBLIC_HEADERS)

    def fetch_hashtag_posts(self, hashtag: str, max_posts: int = 30) -> List[Dict]:
        """抓取指定 hashtag 的公開貼文"""
        tag = hashtag.lstrip("#")
        posts = []

        # 方法一：Threads hashtag 搜尋 API
        posts = self._fetch_via_hashtag_api(tag, max_posts)

        # 若方法一失敗，嘗試方法二
        if not posts:
            posts = self._fetch_via_graphql(tag, max_posts)

        logger.info(f"[Threads] #{tag}: 取得 {len(posts)} 篇貼文")
        return posts

    def _fetch_via_hashtag_api(self, tag: str, max_posts: int) -> List[Dict]:
        """使用 Threads 公開 hashtag API"""
        posts = []
        try:
            def _fetch():
                params = {"query": tag, "count": min(max_posts, 30)}
                resp = self.session.get(
                    THREADS_SEARCH_URL, params=params, timeout=15
                )
                resp.raise_for_status()
                data = resp.json()

                # 解析回傳結構
                items = (
                    data.get("results", [])
                    or data.get("hashtags", [])
                    or data.get("items", [])
                )
                for item in items:
                    post = self._parse_post(item, tag)
                    if post:
                        posts.append(post)
                        self._rate_limit()
                return posts

            return self._retry(_fetch)
        except Exception as e:
            logger.warning(f"[Threads] hashtag API 失敗 #{tag}: {e}")
            return []

    def _fetch_via_graphql(self, tag: str, max_posts: int) -> List[Dict]:
        """備用：Threads GraphQL 公開端點"""
        posts = []
        try:
            payload = {
                "lsd": "AVqbxe3J_YA",
                "variables": json.dumps({
                    "search_surface": "hashtag",
                    "query": f"#{tag}",
                    "count": min(max_posts, 20),
                }),
                "doc_id": "7357407884335963",  # Threads hashtag search doc_id
            }

            def _fetch():
                resp = self.session.post(
                    THREADS_GRAPHQL_URL,
                    data=payload,
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()

                edges = (
                    data.get("data", {})
                    .get("xdt_api__v1__search__topsearch__connection", {})
                    .get("edges", [])
                )
                for edge in edges:
                    node = edge.get("node", {})
                    post = self._parse_graphql_node(node, tag)
                    if post:
                        posts.append(post)
                        self._rate_limit()
                return posts

            return self._retry(_fetch)
        except Exception as e:
            logger.warning(f"[Threads] GraphQL 失敗 #{tag}: {e}")
            return []

    def _parse_post(self, item: Dict, tag: str) -> Dict | None:
        """解析 hashtag API 回傳的貼文物件"""
        try:
            # Threads API 回傳格式不固定，嘗試多個欄位路徑
            text = (
                item.get("caption", {}).get("text", "")
                or item.get("text", "")
                or item.get("content", "")
                or ""
            )
            likes = (
                item.get("like_count", 0)
                or item.get("likes", 0)
                or 0
            )
            comments = (
                item.get("text_post_app_info", {}).get("direct_reply_count", 0)
                or item.get("reply_count", 0)
                or item.get("comments", 0)
                or 0
            )
            ts = item.get("taken_at") or item.get("timestamp") or ""
            if isinstance(ts, (int, float)):
                ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

            return {
                "id": item.get("pk") or item.get("id") or "",
                "platform": "threads",
                "hashtag": f"#{tag}",
                "text": text,
                "likes": int(likes),
                "comments": int(comments),
                "timestamp": str(ts),
                "url": f"https://www.threads.net/search?q=%23{tag}",
            }
        except Exception as e:
            logger.debug(f"[Threads] 解析貼文失敗: {e}")
            return None

    def _parse_graphql_node(self, node: Dict, tag: str) -> Dict | None:
        """解析 GraphQL 回傳的節點"""
        try:
            media = node.get("thread_items", [{}])[0].get("post", node)
            return self._parse_post(media, tag)
        except Exception:
            return None

    def fetch_trending(self) -> List[str]:
        """取得 Threads 目前熱門話題（公開方式）"""
        trending = []
        try:
            # 嘗試抓取 Threads 探索頁的熱門 hashtag
            resp = self.session.get(
                "https://www.threads.net/api/v1/discover/topical_explore/",
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                for item in items:
                    tag = item.get("hashtag", {}).get("name", "")
                    if tag:
                        trending.append(tag)
        except Exception as e:
            logger.info(f"[Threads] 自動探索熱門話題失敗（使用自訂關鍵字）: {e}")
        return trending[:20]
