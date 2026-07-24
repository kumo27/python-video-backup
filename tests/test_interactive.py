import unittest
from unittest.mock import patch

from modules.interactive import Interactive


class BrowserOptAskTest(unittest.TestCase):
    """對Interactive下的browser_opt_ask函式測試"""

    def test_browser_opt_ask_correct(self):
        """有效輸入測試"""
        # 準備
        browser_tuple = Interactive().browser_tuple

        for i, browser in enumerate(browser_tuple):
            interactive = Interactive()

            with (
                self.subTest(i=i, browser=browser),
                patch("modules.interactive.input") as mock_input,
            ):
                mock_input.return_value = str(i)

                # 執行
                interactive._browser_opt_ask()

                # 斷言
                if browser == "不匯入":
                    self.assertEqual(interactive.ydl_update_opts, {})
                else:
                    self.assertEqual(
                        interactive.ydl_update_opts, {"cookiesfrombrowser": (browser,)}
                    )

    def test_browser_opt_ask_error(self):
        """無效輸入測試"""
        # 準備
        interactive = Interactive()

        with (
            patch("modules.interactive.input") as mock_input,
            patch("modules.interactive.answer_error") as mock_answer_error,
            patch("modules.interactive.print") as mock_print,
        ):
            mock_input.return_value = "鳴呼～"

            # 執行
            interactive._browser_opt_ask()

        # 斷言
        self.assertEqual(interactive.ydl_update_opts, {})
        self.assertEqual(mock_answer_error.call_count, 5)
        mock_print.assert_called_once_with("無效輸入過多，使用預設設定")


class DownloaderOptAskTest(unittest.TestCase):
    """對Interactive下的dl_opt_ask函式測試"""

    def test_dl_opt_ask_y(self):
        """有效y輸入測試"""
        # 準備
        test_input = ["y", "Y", "y ", "Y "]

        for user_input in test_input:
            interactive = Interactive()

            with (
                self.subTest(user_input=user_input),
                patch("modules.interactive.input") as mock_input,
            ):
                mock_input.return_value = user_input

                # 執行
                interactive._dl_opt_ask()

                # 斷言
                self.assertEqual(interactive.ydl_update_opts, {"skip_download": True})
                self.assertEqual(interactive.comment_update, True)

    def test_dl_opt_ask_n(self):
        """有效n輸入測試"""
        # 準備
        test_input = ["n", "N", "n ", "N "]

        for user_input in test_input:
            interactive = Interactive()

            with (
                self.subTest(user_input=user_input),
                patch("modules.interactive.input") as mock_input,
            ):
                mock_input.return_value = user_input

                # 執行
                interactive._dl_opt_ask()

                # 斷言
                self.assertEqual(interactive.ydl_update_opts, {})
                self.assertEqual(interactive.comment_update, False)

    def test_dl_opt_ask_error(self):
        """無效輸入測試"""
        # 準備
        interactive = Interactive()

        with (
            patch("modules.interactive.input") as mock_input,
            patch("modules.interactive.answer_error") as mock_answer_error,
            patch("modules.interactive.print") as mock_print,
        ):
            mock_input.return_value = "moshi moshi"

            # 執行
            interactive._dl_opt_ask()

        # 斷言
        self.assertEqual(interactive.ydl_update_opts, {})
        self.assertEqual(mock_answer_error.call_count, 5)
        mock_print.assert_called_once_with("無效輸入過多，使用預設設定")
