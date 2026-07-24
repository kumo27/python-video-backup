import logging
from pathlib import Path

import urllib3.util.connection as urllib3_cn

# 全域變數

# log類
log_dir: Path = Path.cwd() / "log"  # log路徑
log_root: str = "main"  # log根名
fail_urls_log_root: str = "fail_urls"  # 失敗連結log根名

# 檔案類
temp_dir: Path = Path.cwd() / "temp"  # 緩存路徑
download_dir: Path = Path.cwd() / "download"  # 下載路徑
urls_txt_path: Path = Path.cwd() / "urls.txt"  # urls檔案路徑

# 其他
max_workers: int = 3  # 多執行緒數目
urllib3_cn.HAS_IPV6 = False  # 禁止ipv6


class Log:
    """log設定"""

    def __init__(self):
        self.log_dir = log_dir
        self.log_root = log_root
        self.fail_urls_log_root = fail_urls_log_root

        self.log_dir.mkdir(exist_ok=True)

    def full_log(self):
        """主log終端與檔案設定"""
        # 主log初始化
        logger = logging.getLogger(self.log_root)
        logger.setLevel(logging.DEBUG)

        # 終端設定
        terminal_handler = logging.StreamHandler()
        terminal_handler.setLevel(logging.WARNING)
        terminal_fmt = logging.Formatter("[%(levelname)s] %(message)s")
        terminal_handler.setFormatter(terminal_fmt)
        logger.addHandler(terminal_handler)

        # log檔案設定
        file_handler = logging.FileHandler((self.log_dir / "full_log.log"), "w", "utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

    def fail_urls_log(self):
        """失敗連結log設定"""
        # 失敗連結log初始化
        fail_urls_logger = logging.getLogger(self.fail_urls_log_root)
        fail_urls_logger.propagate = False
        fail_urls_logger.setLevel(logging.DEBUG)

        # 失敗連結log檔案設定
        file_handler = logging.FileHandler((self.log_dir / "fail_urls.txt"), "w", "utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter("%(message)s")
        file_handler.setFormatter(file_fmt)
        fail_urls_logger.addHandler(file_handler)
