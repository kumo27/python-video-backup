import logging
import subprocess
from shutil import rmtree
from sys import exit

from . import config
from .tool import answer_error, clear_terminal

logger = logging.getLogger(config.log_root)


def main_init():
    """總初始化"""
    log_init()
    temp_init()
    miss_program = init_check()
    clear_terminal()

    return miss_program


def log_init():
    """log初始化"""
    config.log_dir.mkdir(exist_ok=True)
    config.full_log()
    config.fail_urls_log()


def temp_init():
    """temp資料夾初始化"""
    rmtree(config.temp_dir, ignore_errors=True)
    config.temp_dir.unlink(missing_ok=True)
    config.temp_dir.mkdir(exist_ok=True)


def init_check() -> tuple[str, ...]:
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
