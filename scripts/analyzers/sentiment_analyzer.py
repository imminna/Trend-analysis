import logging
from typing import Dict, Literal
from langdetect import detect, LangDetectException
from snownlp import SnowNLP
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "neutral", "negative"]

_vader = SentimentIntensityAnalyzer()


def detect_language(text: str) -> str:
    """偵測文字語言，回傳 'zh' 或 'en' 或 'other'"""
    if not text or len(text.strip()) < 5:
        return "other"
    try:
        lang = detect(text)
        if lang in ("zh-cn", "zh-tw", "zh"):
            return "zh"
        if lang == "en":
            return "en"
        return "other"
    except LangDetectException:
        return "other"


def analyze_sentiment(text: str) -> Dict:
    """
    分析一段文字的情感，自動偵測語言。
    回傳格式：{"label": "positive"|"neutral"|"negative", "score": 0.0~1.0, "lang": "zh"|"en"|"other"}
    """
    lang = detect_language(text)

    if lang == "zh":
        return _analyze_chinese(text, lang)
    elif lang == "en":
        return _analyze_english(text, lang)
    else:
        # 未知語言嘗試用英文 VADER 分析
        return _analyze_english(text, lang)


def _analyze_chinese(text: str, lang: str) -> Dict:
    """使用 SnowNLP 分析中文情感（0=負面, 1=正面）"""
    try:
        score = SnowNLP(text).sentiments
        if score >= 0.6:
            label = "positive"
        elif score <= 0.4:
            label = "negative"
        else:
            label = "neutral"
        return {"label": label, "score": round(score, 3), "lang": lang}
    except Exception as e:
        logger.warning(f"SnowNLP 分析失敗: {e}")
        return {"label": "neutral", "score": 0.5, "lang": lang}


def _analyze_english(text: str, lang: str) -> Dict:
    """使用 VADER 分析英文/其他語言情感"""
    try:
        scores = _vader.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            label = "positive"
            score = (compound + 1) / 2  # 轉換到 0~1
        elif compound <= -0.05:
            label = "negative"
            score = (compound + 1) / 2
        else:
            label = "neutral"
            score = 0.5
        return {"label": label, "score": round(score, 3), "lang": lang}
    except Exception as e:
        logger.warning(f"VADER 分析失敗: {e}")
        return {"label": "neutral", "score": 0.5, "lang": lang}


def aggregate_sentiments(posts: list) -> Dict:
    """彙整一批貼文的情感分析結果"""
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for post in posts:
        text = post.get("text", "")
        result = analyze_sentiment(text)
        counts[result["label"]] += 1

    total = sum(counts.values()) or 1
    return {
        "positive": round(counts["positive"] / total * 100, 1),
        "neutral": round(counts["neutral"] / total * 100, 1),
        "negative": round(counts["negative"] / total * 100, 1),
    }
