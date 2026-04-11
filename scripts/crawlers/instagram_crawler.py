import logging
import instaloader
from datetime import datetime, timezone
from typing import List, Dict
from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class InstagramCrawler(BaseCrawler):
    """Instagram 爬蟲（訪客模式，不需要登入）"""

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
        logger.info("[Instagram] 訪客模式（每個 hashtag 最多約 12 篇）")

    def fetch_hashtag_posts(self, hashtag: str, max_posts: int = 12) -> List[Dict]:
        """抓取指定 hashtag 的公開貼文（訪客模式）"""
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
        logger.info("[Instagram] 自動探索熱門話題尚未支援，使用自訂關鍵字")
        return []
