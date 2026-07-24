from typing import Any

from .config import urls_txt_path
from .init import answer_error


class Interactive:
    def __init__(self) -> None:
        self.ydl_update_opts: dict[str, Any] = {}  # 參數更新用字典
        self.comment_update: bool = False
        self.urls: list[str] = []
        self.browser_tuple = ("不匯入", "chrome", "edge", "brave", "firefox")  # 瀏覽器選項

    def main_ask(self):
        self._browser_opt_ask()
        self._dl_opt_ask()
        self._urls_file_use_ask()

    def _browser_opt_ask(self):
        # 生成詢問內容
        ask_str = "選擇是否從瀏覽器匯入cookie:\n"
        for i, browser in enumerate(self.browser_tuple):
            ask_str += f"{i}: {browser}\n"
        ask_str += ": "

        # 選擇從瀏覽器匯入cookie
        for _ in range(5):
            browser_key = input(ask_str).strip()
            if browser_key.isdecimal() and int(browser_key) < len(self.browser_tuple):
                if int(browser_key) != 0:
                    self.ydl_update_opts["cookiesfrombrowser"] = (
                        self.browser_tuple[int(browser_key)],
                    )
                break
            answer_error()
        else:
            print("無效輸入過多，使用預設設定")

    def _dl_opt_ask(self):
        # 僅更新留言詢問
        for _ in range(5):
            answer = input("是否僅更新留言(y/n): ").strip().lower()
            if answer == "y":
                self.ydl_update_opts["skip_download"] = True
                self.comment_update = True
                break
            elif answer == "n":
                break
            answer_error()
        else:
            print("無效輸入過多，使用預設設定")

    def _urls_file_use_ask(self):
        # 判斷有沒有連結檔
        if urls_txt_path.is_file():
            for _ in range(5):
                answer = input("是否使用urls.txt(y/n): ").strip().lower()
                if answer == "y":
                    with urls_txt_path.open(encoding="utf-8") as f:
                        self.urls = f.readlines()
                    break
                elif answer == "n":
                    break
                answer_error()
            else:
                print("無效輸入過多，使用預設設定")

        if self.urls == []:
            self.urls = [input("請輸入影片網址: ")]
