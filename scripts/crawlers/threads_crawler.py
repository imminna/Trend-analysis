import re
import requests
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

THREADS_BASE_URL = "https://www.threads.net"
THREADS_SEARCH_URL = "https://www.threads.net/api/v1/search/hashtags/"
THREADS_GRAPHQL_URL = "https://www.threads.net/api/graphql"

# 基本 headers（不含動態 token）
BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "x-ig-app-id": "238260118697367",
    "Referer": "https://www.threads.net/",
    "Origin": "https://www.threads.net",
}

# LSD token 解析 patterns（依優先順序）
# Meta 頁面常見格式：["LSD",[],{"token":"xxx"}] 或 ["LSD",[],[],{"token":"xxx"}]
LSD_PATTERNS = [
    r'"LSD"\s*,\s*(?:\[\]\s*,\s*)+\{"token"\s*:\s*"([^"]+)"',
    r'"lsd"\s*,\s*(?:\[\]\s*,\s*)+\{"token"\s*:\s*"([^"]+)"',
    r'&lsd=([A-Za-z0-9_\-]+)',
    r'name="lsd"\s+value="([^"]+)"',
    r'"lsd"\s*:\s*"([A-Za-z0-9_\-]{6,})"',
]


class ThreadsCrawler(BaseCrawler):
    """Threads 公開爬蟲，動態取得 LSD token，不需要 access token"""

    def __init__(self):
        super().__init__("threads")
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self._lsd_token: Optional[str] = None
        # 初始化：取得 cookies 與 LSD token
        self._init_session()

    def _init_session(self):
        """
        對 threads.net 首頁發一次 GET，取得：
        1. Session cookies（csrftoken 等）
        2. 動態 LSD token（嵌在 HTML 中的 CSRF 保護 token）
        """
        try:
            resp = self.session.get(THREADS_BASE_URL, timeout=15)
            resp.raise_for_status()
            self._lsd_token = self._extract_lsd(resp.text)
            if self._lsd_token:
                logger.info(f"[Threads] 成功取得 LSD token: {self._lsd_token[:8]}…")
            else:
                logger.warning("[Threads] 無法解析 LSD token，將嘗試不帶 token 的請求")
        except Exception as e:
            logger.warning(f"[Threads] 初始化 session 失敗: {e}")

    def _extract_lsd(self, html: str) -> Optional[str]:
        """從 HTML 中解析 LSD token"""
        for pattern in LSD_PATTERNS:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    def _api_headers(self) -> Dict:
        """組合帶有 LSD token 的 API 請求 headers"""
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "x-ig-app-id": "238260118697367",
            "Referer": "https://www.threads.net/",
            "Origin": "https://www.threads.net",
        }
        if self._lsd_token:
            headers["x-fb-lsd"] = self._lsd_token
        return headers

    # ──────────────────────────────────────────────
    # 公開介面
    # ──────────────────────────────────────────────

    def fetch_hashtag_posts(self, hashtag: str, max_posts: int = 30) -> List[Dict]:
        """抓取指定 hashtag 的公開貼文（依序嘗試兩種 API）"""
        tag = hashtag.lstrip("#")

        posts = self._fetch_via_hashtag_api(tag, max_posts)
        if not posts:
            posts = self._fetch_via_graphql(tag, max_posts)

        logger.info(f"[Threads] #{tag}: 取得 {len(posts)} 篇貼文")
        return posts

    def fetch_trending(self) -> List[str]:
        """取得 Threads 目前熱門話題"""
        trending = []
        try:
            resp = self.session.get(
                f"{THREADS_BASE_URL}/api/v1/discover/topical_explore/",
                headers=self._api_headers(),
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("items", []):
                    tag = item.get("hashtag", {}).get("name", "")
                    if tag:
                        trending.append(tag)
        except Exception as e:
            logger.info(f"[Threads] 自動探索熱門話題失敗（使用自訂關鍵字）: {e}")
        return trending[:20]

    # ──────────────────────────────────────────────
    # 內部 API 方法
    # ──────────────────────────────────────────────

    def _fetch_via_hashtag_api(self, tag: str, max_posts: int) -> List[Dict]:
        """方法一：Threads hashtag 搜尋 REST API"""
        posts: List[Dict] = []
        try:
            def _fetch():
                params = {"query": tag, "count": min(max_posts, 30)}
                resp = self.session.get(
                    THREADS_SEARCH_URL,
                    params=params,
                    headers=self._api_headers(),
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()

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
        """方法二：備用 Threads GraphQL 公開端點"""
        posts: List[Dict] = []
        if not self._lsd_token:
            logger.warning(f"[Threads] 沒有 LSD token，跳過 GraphQL 請求 #{tag}")
            return []
        try:
            payload = {
                "lsd": self._lsd_token,
                "variables": json.dumps({
                    "search_surface": "hashtag",
                    "query": f"#{tag}",
                    "count": min(max_posts, 20),
                }),
                "doc_id": "7357407884335963",
            }

            def _fetch():
                resp = self.session.post(
                    THREADS_GRAPHQL_URL,
                    data=payload,
                    headers=self._api_headers(),
                    timeout=15,
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

    # ──────────────────────────────────────────────
    # 解析器
    # ──────────────────────────────────────────────

    def _parse_post(self, item: Dict, tag: str) -> Optional[Dict]:
        """解析 hashtag API 回傳的貼文物件"""
        try:
            text = (
                item.get("caption", {}).get("text", "")
                or item.get("text", "")
                or item.get("content", "")
                or ""
            )
            likes = item.get("like_count") or item.get("likes") or 0
            comments = (
                item.get("text_post_app_info", {}).get("direct_reply_count")
                or item.get("reply_count")
                or item.get("comments")
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

    def _parse_graphql_node(self, node: Dict, tag: str) -> Optional[Dict]:
        """解析 GraphQL 回傳的節點"""
        try:
            media = node.get("thread_items", [{}])[0].get("post", node)
            return self._parse_post(media, tag)
        except Exception:
            return None
