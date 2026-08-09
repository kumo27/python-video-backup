import unittest

from modules.config import fail_urls_log_root, log_root
from modules.process.preprocess import __name__ as module_name
from modules.process.preprocess import urls_classification


class UrlsClassificationTest(unittest.TestCase):
    """影片分類測試"""

    def test_url_no_suffix(self):
        """無後綴連結測試"""
        # 準備
        test_input = ["https://www.youtube.com/watch?v=2_AkQJVOO5b"]
        result_playlist_urls = []
        result_video_urls = ["https://youtube.com/watch?v=2_AkQJVOO5b"]
        result = (result_playlist_urls, result_video_urls)

        # 執行
        url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(url_return, result)

    def test_url_suffix(self):
        """帶後綴連結測試"""
        # 準備
        test_input = ["https://www.youtube.com/watch?v=m8ppen-3asc&list=2_6MvfpgKqK3S&index=1"]
        result_playlist_urls = []
        result_video_urls = ["https://youtube.com/watch?v=m8ppen-3asc"]
        result = (result_playlist_urls, result_video_urls)

        # 執行
        url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(url_return, result)

    def test_url_share(self):
        """分享按鈕中的連結測試"""
        # 準備
        test_input = ["https://youtu.be/2R2X-3ii2_4?si=PhHtf2Y3WcXUyO-3"]
        result_playlist_urls = []
        result_video_urls = ["https://youtu.be/2R2X-3ii2_4"]
        result = (result_playlist_urls, result_video_urls)

        # 執行
        url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(url_return, result)

    def test_userid_channel_no_suffix(self):
        """無後綴頻道連結(userid)測試"""
        # 準備
        test_input = ["https://www.youtube.com/@this.is.test"]
        result_playlist_urls = ["https://youtube.com/@this.is.test"]
        result_video_urls = []
        result = (result_playlist_urls, result_video_urls)

        # 執行
        url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(url_return, result)

    def test_userid_channel_suffix(self):
        """帶後綴頻道連結(userid)測試"""
        # 準備
        test_input = ["https://www.youtube.com/@this-is-test/streams"]
        result_playlist_urls = ["https://youtube.com/@this-is-test"]
        result_video_urls = []
        result = (result_playlist_urls, result_video_urls)

        # 執行
        url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(url_return, result)

    def test_old_channel(self):
        """頻道連結(舊版連結)測試"""
        # 準備
        test_input = ["https://www.youtube.com/channel/UCcBAsE62DG0h1IjKLmNOP3q"]
        result_playlist_urls = ["https://youtube.com/channel/UCcBAsE62DG0h1IjKLmNOP3q"]
        result_video_urls = []
        result = (result_playlist_urls, result_video_urls)

        # 執行
        url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(url_return, result)

    def test_playlist_no_suffix(self):
        """無後綴播放清單連結測試"""
        # 準備
        test_input = ["https://www.youtube.com/playlist?list=PL2_7G3SE0rKmou0DOH-3UvWxYZ1234567"]
        result_playlist_urls = [
            "https://youtube.com/playlist?list=PL2_7G3SE0rKmou0DOH-3UvWxYZ1234567"
        ]
        result_video_urls = []
        result = (result_playlist_urls, result_video_urls)

        # 執行
        url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(url_return, result)

    def test_playlist_suffix(self):
        """帶後綴播放清單連結測試"""
        # 準備
        test_input = [
            "https://youtube.com/playlist?list=PLABCDefGHIJKLmnopq0RSTUvWxYZ12345&si=abcdefghijklmn-0"
        ]
        result_playlist_urls = [
            "https://youtube.com/playlist?list=PLABCDefGHIJKLmnopq0RSTUvWxYZ12345"
        ]
        result_video_urls = []
        result = (result_playlist_urls, result_video_urls)

        # 執行
        url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(url_return, result)

    def test_error_url(self):
        """無效連結測試"""
        # 準備
        test_input = ["https://youtube.com/asjidjiww"]
        result_playlist_urls = []
        result_video_urls = []
        result = (result_playlist_urls, result_video_urls)

        # 執行
        with self.assertLogs() as loggers:
            url_return = urls_classification(test_input)

        # 斷言
        self.assertEqual(
            loggers.output,
            [
                f"ERROR:{log_root}.{module_name}:程式目前可能無法下載「 {test_input[0]} 」，請考慮將網址回報，非常抱歉",  # noqa: E501
                f"ERROR:{fail_urls_log_root}:{test_input[0]}",
            ],
        )
        self.assertEqual(url_return, result)
