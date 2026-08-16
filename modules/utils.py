import os
import subprocess
from time import sleep


def clear_terminal() -> None:
    """終端清理"""
    subprocess.run("cls" if os.name == "nt" else "clear")


def answer_error() -> None:
    """輸入錯誤統一處理"""
    clear_terminal()
    print("無效參數")
    sleep(1)
