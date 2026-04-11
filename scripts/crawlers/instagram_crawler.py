import logging
import instaloader
from datetime import datetime, timezone
from typing import List, Dict
from .base_crawler import BaseCrawler
from config.settings import IG_SESSION_ID

logger = logging.getLogger(__name__)


class InstagramCrawler(BaseCrawler):
    """Instagram 爬蟲，使用 instaloader 並透過 session cookie 認證"""

    def __init__(self):
        super().__init__("instagram")
        self.loader = instaloader.Instaloader(
            quiet=True,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
        )
        self._login()

    def _login(self):
        """透過 session cookie 登入，不需要密碼"""
        if not IG_SESSION_ID:
            logger.warning("[Instagram] 未設定 IG_SESSION_ID，將以訪客模式運行（資料有限）")
            return
        try:
            # instaloader 支援直接設定 session cookie
            self.loader.context._session.cookies.set(
                "sessionid", IG_SESSION_ID, domain=".instagram.com"
            )
            self.loader.context.username = "user"  # placeholder
            logger.info("[Instagram] Session cookie 載入成功")
        except Exception as e:
            logger.error(f"[Instagram] 登入失敗: {e}")

    def fetch_hashtag_posts(self, hashtag: str, max_posts: int = 50) -> List[Dict]:
        """抓取指定 hashtag 的最新貼文"""
        posts = []
        tag = hashtag.lstrip("#")

        def _fetch():
            hashtag_obj = instaloader.Hashtag.from_name(self.loader.context, tag)
            count = 0
            for post in hashtag_obj.get_posts():
                if count >= max_posts:
                    break
                posts.append({
                    "id": post.shortcode,
                    "platform": "instagram",
                    "hashtag": f"#{tag}",
                    "text": post.caption or "",
                    "likes": post.likes,
                    "comments": post.comments,
                    "timestamp": post.date_utc.replace(tzinfo=timezone.utc).isoformat(),
                    "url": f"https://www.instagram.com/p/{post.shortcode}/",
                })
                count += 1
                self._rate_limit()
            return posts

        try:
            return self._retry(_fetch)
        except Exception as e:
            logger.error(f"[Instagram] 抓取 #{tag} 失敗: {e}")
            return []

    def fetch_trending(self) -> List[str]:
        """
        IG 沒有公開 trending API，這裡回傳空清單。
        實際使用時可透過 Explore 頁面解析，但需要更複雜的 session 處理。
        """
        logger.info("[Instagram] 自動探索熱門話題尚未支援，使用自訂關鍵字")
        return []
