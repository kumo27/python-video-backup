import logging
import logging.config
import subprocess
from sys import exit
from time import sleep

from .config import LOG_DIR, LOGGING_CONFIG
from .utils import answer_error, clear_terminal

logger = logging.getLogger(__name__)


def main_init() -> frozenset[str]:
    """總初始化"""
    log_init()
    miss_program: frozenset[str] = init_check()
    clear_terminal()

    return miss_program


def log_init() -> None:
    """log初始化"""
    LOG_DIR.mkdir(exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)


def init_check() -> frozenset[str]:
    """運行環境檢查"""
    check_list: dict[str, tuple[str, str]] = {
        "ffmpeg": ("ffmpeg", "-h"),
        "par2": ("par2", "-h"),
        "mkvpropedit": ("mkvpropedit", "-h"),
        "cjxl": ("cjxl", "-h"),
    }

    miss_program: set[str] = set()
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
            for _ in range(3):
                answer: str = input("忽略錯誤繼續？(y/n): ").strip().lower()

                if answer == "y":
                    break
                elif answer == "n":
                    exit()

                answer_error()
            else:
                print("無效輸入過多，使用預設設定(忽略錯誤)")
                sleep(2)

            miss_program.add(program)

    return frozenset(miss_program)
