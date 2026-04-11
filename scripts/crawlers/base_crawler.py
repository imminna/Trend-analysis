import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from config.settings import RATE_LIMIT_MIN, RATE_LIMIT_MAX, MAX_RETRIES

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """爬蟲基底類別，提供 rate limiting 和 retry 邏輯"""

    def __init__(self, platform: str):
        self.platform = platform

    def _rate_limit(self):
        """隨機延遲，避免被平台偵測"""
        delay = random.uniform(RATE_LIMIT_MIN, RATE_LIMIT_MAX)
        time.sleep(delay)

    def _retry(self, func, *args, **kwargs) -> Any:
        """指數退避 retry 包裝器"""
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"[{self.platform}] 失敗 {MAX_RETRIES} 次後放棄: {e}")
                    raise
                wait = 2 ** attempt * random.uniform(1.0, 2.0)
                logger.warning(f"[{self.platform}] 第 {attempt + 1} 次失敗，{wait:.1f} 秒後重試: {e}")
                time.sleep(wait)

    @abstractmethod
    def fetch_hashtag_posts(self, hashtag: str, max_posts: int) -> List[Dict]:
        """抓取指定 hashtag 的貼文"""
        pass

    @abstractmethod
    def fetch_trending(self) -> List[str]:
        """取得平台當前熱門 hashtag 清單"""
        pass
