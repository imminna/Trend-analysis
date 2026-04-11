"""
main.py — 爬蟲主入口
用法：
  python main.py              # 正常執行
  python main.py --dry-run    # 只輸出 JSON 到 stdout，不寫檔
  python main.py --keywords "咖啡,科技"  # 額外指定關鍵字
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from collections import defaultdict

# 將 scripts/ 加入 Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import DATA_DIR, load_keywords_config
from crawlers.instagram_crawler import InstagramCrawler
from crawlers.threads_crawler import ThreadsCrawler
from analyzers.sentiment_analyzer import aggregate_sentiments
from analyzers.keyword_extractor import extract_keywords
from analyzers.trend_calculator import aggregate_topic_stats, rank_topics
from utils.data_writer import (
    write_trending, write_history, write_keywords,
    write_sentiment, write_meta
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("main")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只輸出 JSON，不寫入檔案")
    parser.add_argument("--keywords", type=str, default="", help="額外關鍵字（逗號分隔）")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_keywords_config()

    # 整合關鍵字：自訂 + 命令列傳入
    keywords = list(config.get("custom_keywords", []))
    if args.keywords:
        keywords += [k.strip() for k in args.keywords.split(",") if k.strip()]
    keywords = list(dict.fromkeys(keywords))  # 去重保序

    platforms = config.get("platforms", ["instagram", "threads"])
    max_posts = config.get("max_posts_per_tag", 50)

    logger.info(f"追蹤關鍵字: {keywords}")
    logger.info(f"啟用平台: {platforms}")

    # 初始化爬蟲
    crawlers = []
    if "instagram" in platforms:
        try:
            crawlers.append(InstagramCrawler())
        except Exception as e:
            logger.error(f"IG 爬蟲初始化失敗: {e}")
    if "threads" in platforms:
        try:
            crawlers.append(ThreadsCrawler())
        except Exception as e:
            logger.error(f"Threads 爬蟲初始化失敗: {e}")

    # 抓取自動熱門話題（各平台）
    auto_tags = []
    if config.get("auto_discover", False):
        for crawler in crawlers:
            auto_tags += crawler.fetch_trending()
        auto_tags = list(set(auto_tags))
        logger.info(f"自動發現熱門話題: {auto_tags[:10]}")

    all_keywords = list(dict.fromkeys(keywords + auto_tags))

    # 蒐集所有貼文（按 hashtag 分組）
    posts_by_tag = defaultdict(list)
    all_posts = []

    for tag in all_keywords:
        hashtag = f"#{tag.lstrip('#')}"
        for crawler in crawlers:
            posts = crawler.fetch_hashtag_posts(hashtag, max_posts)
            posts_by_tag[hashtag].extend(posts)
            all_posts.extend(posts)
        logger.info(f"{hashtag}: 共 {len(posts_by_tag[hashtag])} 篇貼文")

    # 計算趨勢排行
    topic_stats = [
        aggregate_topic_stats(posts, tag)
        for tag, posts in posts_by_tag.items()
    ]
    ranked_topics = rank_topics(topic_stats)

    # 情感分析
    overall_sentiment = aggregate_sentiments(all_posts)
    sentiment_by_topic = {
        tag: aggregate_sentiments(posts)
        for tag, posts in posts_by_tag.items()
    }

    # 關鍵字提取
    keywords_data = extract_keywords(all_posts, top_n=60)

    # 輸出結果
    if args.dry_run:
        result = {
            "trending": {"topics": ranked_topics},
            "sentiment": {"overall": overall_sentiment, "by_topic": sentiment_by_topic},
            "keywords": {"words": keywords_data},
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        logger.info("--dry-run 模式：結果已輸出到 stdout，未寫入檔案")
    else:
        write_trending(DATA_DIR, ranked_topics)
        write_history(DATA_DIR, ranked_topics)
        write_sentiment(DATA_DIR, overall_sentiment, sentiment_by_topic)
        write_keywords(DATA_DIR, keywords_data)
        write_meta(DATA_DIR, status="ok")
        logger.info("所有資料已寫入 data/ 目錄")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"執行失敗: {e}", exc_info=True)
        # 寫入錯誤狀態，讓前端能顯示警告
        from utils.data_writer import write_meta
        write_meta(DATA_DIR, status="error", error=str(e))
        sys.exit(1)
