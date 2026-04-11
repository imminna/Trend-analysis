import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def _load_json(path: Path) -> Any:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"已寫入: {path}")


def write_trending(data_dir: Path, topics: List[Dict]):
    """寫入 trending.json"""
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "topics": topics,
    }
    _save_json(data_dir / "trending.json", payload)


def write_history(data_dir: Path, topics: List[Dict], history_days: int = 30):
    """
    更新 history.json。
    保留最近 history_days 天的資料，每次執行追加今日數據。
    """
    history_path = data_dir / "history.json"
    existing = _load_json(history_path) or {"dates": [], "topics": {}}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 加入今日日期（避免重複）
    if today not in existing["dates"]:
        existing["dates"].append(today)

    # 加入今日各話題分數
    for topic in topics:
        tag = topic["tag"]
        if tag not in existing["topics"]:
            existing["topics"][tag] = []
        # 確保長度與 dates 一致（補零）
        while len(existing["topics"][tag]) < len(existing["dates"]) - 1:
            existing["topics"][tag].append(0)
        existing["topics"][tag].append(topic.get("trend_score", 0))

    # 只保留最近 history_days 天
    if len(existing["dates"]) > history_days:
        excess = len(existing["dates"]) - history_days
        existing["dates"] = existing["dates"][excess:]
        for tag in existing["topics"]:
            existing["topics"][tag] = existing["topics"][tag][excess:]

    _save_json(history_path, existing)


def write_keywords(data_dir: Path, keywords: List[Dict]):
    """寫入 keywords.json"""
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "words": keywords,
    }
    _save_json(data_dir / "keywords.json", payload)


def write_sentiment(data_dir: Path, overall: Dict, by_topic: Dict):
    """寫入 sentiment.json"""
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "overall": overall,
        "by_topic": by_topic,
    }
    _save_json(data_dir / "sentiment.json", payload)


def write_meta(data_dir: Path, status: str = "ok", error: str = ""):
    """寫入 meta.json（狀態資訊）"""
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "error": error,
    }
    _save_json(data_dir / "meta.json", payload)
