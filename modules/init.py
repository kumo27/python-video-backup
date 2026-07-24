import logging
import os
import subprocess
from shutil import rmtree
from sys import exit
from time import sleep

from .config import Log, log_root, temp_dir

logger = logging.getLogger(log_root)


def clear_terminal():
    """終端清理"""
    subprocess.run("cls" if os.name == "nt" else "clear")


def answer_error():
    """輸入錯誤統一處理"""
    clear_terminal()
    print("無效參數")
    sleep(1)


class Init:
    """初始化模組"""

    def __init__(self) -> None:
        self._log_init()

    def main_init(self):
        """總初始化"""
        self._temp_init()
        miss_program = self._init_check()
        clear_terminal()

        return miss_program

    def _log_init(self):
        """log初始化"""
        log = Log()
        log.full_log()
        log.fail_urls_log()

    def _temp_init(self):
        """temp資料夾初始化"""
        rmtree(temp_dir, ignore_errors=True)
        temp_dir.unlink(missing_ok=True)
        temp_dir.mkdir(exist_ok=True)

    def _init_check(self) -> tuple[str, ...]:
        """運行環境檢查"""
        check_list = {
            "ffmpeg": ("ffmpeg", "-h"),
            "par2": ("par2", "-h"),
            "mkvpropedit": ("mkvpropedit", "-h"),
            "cjxl": ("cjxl", "-h"),
        }

        miss_program: list[str] = []
        for program, cmd in check_list.items():
            try:
                subprocess.run(cmd, capture_output=True)
            except FileNotFoundError:
                clear_terminal()
                # 如果ffmpeg錯誤直接停止
                if program == "ffmpeg":
                    logger.exception(f"未找到{program} 無法繼續運行")
                    exit()

                # 紀錄錯誤並決定是否忽略錯誤
                logger.error(f"依賴項{program} 未找到，部份程式無法執行")
                while True:
                    answer = input("忽略錯誤繼續？(y/n): ").strip().lower()
                    if answer == "y":
                        miss_program.append(program)
                        break
                    elif answer == "n":
                        exit()

                    answer_error()

        return tuple(miss_program)
