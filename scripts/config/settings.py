import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = Path(__file__).parent

# 從環境變數讀取認證資訊（GitHub Secrets）
IG_SESSION_ID = os.environ.get("IG_SESSION_ID", "")
THREADS_TOKEN = os.environ.get("THREADS_TOKEN", "")

# 爬蟲設定
RATE_LIMIT_MIN = 2.0   # 最小間隔秒數
RATE_LIMIT_MAX = 5.0   # 最大間隔秒數
MAX_RETRIES = 3
HISTORY_DAYS = 30      # 保留歷史天數

# 載入關鍵字設定
def load_keywords_config():
    config_path = CONFIG_DIR / "keywords.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
