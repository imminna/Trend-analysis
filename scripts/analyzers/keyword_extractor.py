import re
import logging
import jieba
import jieba.analyse
import nltk
from typing import List, Dict
from langdetect import detect, LangDetectException
from collections import Counter

logger = logging.getLogger(__name__)

# 確保 nltk 資料已下載
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

EN_STOPWORDS = set(stopwords.words("english"))
ZH_STOPWORDS = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一個", "上", "也", "很", "到", "說", "要", "去", "你", "會", "著", "沒有", "看", "好", "自己", "這"}


def extract_keywords(posts: List[Dict], top_n: int = 50) -> List[Dict]:
    """
    從一批貼文中提取高頻關鍵字，混合中英文。
    回傳格式：[{"text": "keyword", "value": frequency}, ...]
    """
    all_texts = " ".join(post.get("text", "") for post in posts)
    if not all_texts.strip():
        return []

    zh_words = _extract_chinese_keywords(all_texts)
    en_words = _extract_english_keywords(all_texts)

    # 合併計數
    combined = Counter(zh_words) + Counter(en_words)

    # 過濾太短的詞
    filtered = {k: v for k, v in combined.items() if len(k) >= 2}

    # 取前 top_n，按頻率排序
    sorted_keywords = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # 正規化 value 到 10~100 範圍（用於字雲視覺化）
    if not sorted_keywords:
        return []
    max_val = sorted_keywords[0][1]
    return [
        {"text": word, "value": max(10, round(count / max_val * 100))}
        for word, count in sorted_keywords
    ]


def _extract_chinese_keywords(text: str) -> Counter:
    """使用 jieba TF-IDF 提取中文關鍵字"""
    try:
        keywords = jieba.analyse.extract_tags(text, topK=80, withWeight=True)
        result = Counter()
        for word, weight in keywords:
            if word not in ZH_STOPWORDS and len(word) >= 2:
                result[word] = int(weight * 100)
        return result
    except Exception as e:
        logger.warning(f"jieba 提取失敗: {e}")
        return Counter()


def _extract_english_keywords(text: str) -> Counter:
    """使用 nltk 提取英文關鍵字"""
    try:
        # 只保留英文部分
        en_text = re.sub(r"[^\x00-\x7F]+", " ", text)
        tokens = word_tokenize(en_text.lower())
        # 過濾停用詞、標點、數字
        words = [
            w for w in tokens
            if w.isalpha() and w not in EN_STOPWORDS and len(w) >= 3
        ]
        return Counter(words)
    except Exception as e:
        logger.warning(f"nltk 提取失敗: {e}")
        return Counter()
