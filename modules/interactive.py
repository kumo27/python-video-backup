from typing import Any

from .config import urls_txt_path
from .utils import answer_error


class Interactive:
    """涉及使用者互動的類"""

    def __init__(self) -> None:
        self.ydl_update_opts: dict[str, Any] = {}  # 參數更新用字典
        self.comment_update: bool = False
        self.urls: list[str] = []
        self.browser_tuple = ("不匯入", "chrome", "edge", "brave", "firefox")  # 瀏覽器選項

    def main_ask(self) -> None:
        self._browser_opt_ask()
        self._dl_opt_ask()
        self._urls_file_use_ask()

    def _browser_opt_ask(self) -> None:
        # 生成詢問內容
        ask_list: list[str] = ["選擇是否從瀏覽器匯入cookie:"]
        ask_list += [f"{i}: {browser}" for i, browser in enumerate(self.browser_tuple)]
        ask_list.append(": ")

        ask_str: str = "\n".join(ask_list)

        # 選擇從瀏覽器匯入cookie
        for _ in range(5):
            try:
                browser_key: int = int(input(ask_str).strip())
            except ValueError:
                answer_error()
                continue

            if browser_key == 0:
                break
            elif 0 < browser_key < len(self.browser_tuple):
                self.ydl_update_opts["cookiesfrombrowser"] = (self.browser_tuple[browser_key],)
                break

            answer_error()
        else:
            print("無效輸入過多，使用預設設定")

    def _dl_opt_ask(self) -> None:
        # 僅更新留言詢問
        for _ in range(5):
            answer: str = input("是否僅更新留言(y/n): ").strip().lower()

            if answer == "y":
                self.ydl_update_opts["skip_download"] = True
                self.comment_update = True
                break
            elif answer == "n":
                break

            answer_error()
        else:
            print("無效輸入過多，使用預設設定")

    def _urls_file_use_ask(self) -> None:
        # 判斷有沒有連結檔
        if urls_txt_path.is_file():
            for _ in range(5):
                answer: str = input("是否使用urls.txt(y/n): ").strip().lower()

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
