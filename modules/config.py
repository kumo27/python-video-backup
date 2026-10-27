from pathlib import Path
from typing import Any

import urllib3.util.connection as urllib3_cn

# 全域變數

# log類
LOG_DIR: Path = Path.cwd() / "log"  # log路徑
FAIL_URLS_LOG_ROOT: str = "fail_urls"  # 失敗連結log根名

# 檔案類
DOWNLOAD_DIR: Path = Path.cwd() / "download"  # 下載路徑
URLS_TXT_PATH: Path = Path.cwd() / "urls.txt"  # urls檔案路徑

# 其他
MAX_WORKERS: int = 3  # 多執行緒數目
urllib3_cn.HAS_IPV6 = False  # 禁止ipv6

# log設定
LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "terminal": {
            "format": "[%(levelname)s] %(message)s",
        },
        "full_log": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        },
        "fail_url": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "terminal": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "terminal",
        },
        "full_log_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "full_log.log",
            "mode": "w",
            "encoding": "utf-8",
            "level": "DEBUG",
            "formatter": "full_log",
        },
        "fail_urls_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "fail_urls.txt",
            "mode": "w",
            "encoding": "utf-8",
            "level": "DEBUG",
            "formatter": "fail_url",
        },
    },
    "loggers": {
        "modules": {
            "level": "DEBUG",
            "handlers": ["terminal", "full_log_file"],
        },
        FAIL_URLS_LOG_ROOT: {
            "level": "DEBUG",
            "handlers": ["fail_urls_file"],
            "propagate": False,
        },
    },
}
