import math
import logging
from datetime import datetime, timezone
from typing import List, Dict

logger = logging.getLogger(__name__)


def calculate_trend_score(post: Dict) -> float:
    """
    計算單篇貼文熱度分數。
    公式：(likes + comments*2) / (hours_elapsed + 2)^1.5
    時間衰減讓新貼文有更高的分數。
    """
    likes = post.get("likes", 0)
    comments = post.get("comments", 0)
    raw_score = likes * 1.0 + comments * 2.0

    # 計算貼文發佈距今幾小時
    try:
        ts = post.get("timestamp", "")
        if ts:
            post_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            hours_elapsed = max(0, (now - post_time).total_seconds() / 3600)
        else:
            hours_elapsed = 24  # 預設 24 小時前
    except Exception:
        hours_elapsed = 24

    return raw_score / math.pow(hours_elapsed + 2, 1.5)


def aggregate_topic_stats(posts: List[Dict], hashtag: str) -> Dict:
    """彙整一個話題的所有貼文統計"""
    if not posts:
        return {
            "tag": hashtag,
            "count": 0,
            "trend_score": 0.0,
            "total_likes": 0,
            "total_comments": 0,
            "source": [],
        }

    total_score = sum(calculate_trend_score(p) for p in posts)
    platforms = list(set(p.get("platform", "") for p in posts))

    return {
        "tag": hashtag,
        "count": len(posts),
        "trend_score": round(total_score, 2),
        "total_likes": sum(p.get("likes", 0) for p in posts),
        "total_comments": sum(p.get("comments", 0) for p in posts),
        "source": platforms,
    }


def rank_topics(topic_stats: List[Dict]) -> List[Dict]:
    """
    對所有話題按 trend_score 降序排列，
    計算相對於最高分的百分比 change 欄位。
    """
    if not topic_stats:
        return []

    sorted_topics = sorted(topic_stats, key=lambda x: x["trend_score"], reverse=True)
    max_score = sorted_topics[0]["trend_score"] or 1

    for i, topic in enumerate(sorted_topics):
        # change 欄位：與第二名的相對差距（第一名顯示絕對分數百分比）
        topic["rank"] = i + 1
        topic["change"] = f"+{round(topic['trend_score'] / max_score * 100)}%"

    return sorted_topics
