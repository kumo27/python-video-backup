import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

logger = logging.getLogger(__name__)


class DL:
    """下載模組"""

    def __init__(self, ydl_update_opts: dict) -> None:
        self.error_dict: dict[str, str] = {
            "Sign in to confirm you’re not a bot.": "youtube要求登入，請考慮匯入瀏覽器cookie",
            "HTTP Error 403: Forbidden": "error 403，禁止訪問，如果先前未匯入cookie請嘗試匯入",
            "Read timed out.": "網路連線逾時，請檢查網路後再試一次",
            "Failed to resolve": "解析失敗，請檢查網路後再試一次",
            "is not a valid URL": "無效連結，請檢查連結後再試一次",
            "Connection reset by peer": "error 104，連線被重置，請稍後重試",
            "HTTP Error 400: Bad Request": "error 400，請求錯誤，可能是網路或網址問題，請檢查以上兩者後重試",  # noqa: E501
            "Private video.": "私人影片，如果你帳戶有能力觀看，請嘗試匯入cookie",
            "Video unavailable. This video is private": "私人影片，無法下載",
            "This live event will begin in": "直播將於未來開始，目前無法下載",
            "Join this channel to get access to members-only content": "加入頻道會員，下載會員影片",
        }  # 錯誤字典
        self.ydl_opts: dict[str, Any] = {
            "format": "bv+ba",  # 品質控制
            "merge_output_format": "mkv",  # 輸出mkv
            "format_sort": ("res", "vcodec:avc+vp9"),  # 微調後的排序
            "writeinfojson": True,  # 寫入影片資訊
            "getcomments": True,  # 寫入留言
            "writesubtitles": True,  # 寫入字幕
            "subtitleslangs": ["all"],  # 指定字幕範圍(全部，包含聊天室)
            "noplaylist": True,  # 防止下載帶播放清單的影片
            "quiet": True,  # 不輸出終端
            "noprogress": True,  #  不輸出進度條
            "no_warnings": True,  # 不要警告
            **ydl_update_opts,  # 更新過來的字典
        }  # 下載選項

    def get_playlist_url(self, url: str) -> tuple[str, ...] | None:
        """取得播放清單內的獨立影片連結"""
        # 變數定義
        new_url: list[str] = []  # 後續回傳的列表
        playlist_dl_opts: dict[str, Any] = {
            **self.ydl_opts,
            "extract_flat": True,
            "skip_download": True,  # 跳過下載
            "writeinfojson": False,
        }  # 播放清單資訊下載用

        with YoutubeDL(playlist_dl_opts) as ydl:  # pyright: ignore[reportArgumentType]
            try:
                logger.debug("解析播放清單")
                info = ydl.extract_info(url, download=False)
            except DownloadError as e:
                self._error_message(e)
                return None

        # 處理獲取的字典資料
        for top_entries in info["entries"]:  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if "entries" in top_entries:
                new_url += [entries["url"] for entries in top_entries["entries"]]  # pyright: ignore[reportAssignmentType, reportTypedDictNotRequiredAccess]
            else:
                new_url.append(top_entries["url"])  # pyright: ignore[reportTypedDictNotRequiredAccess, reportArgumentType]

        logger.debug("返回影片列表")
        return tuple(new_url)

    def download(self, url: str, tmp_dir: Path) -> bool:
        """影片下載與影片資料讀取"""
        # 變數定義
        video_info: dict = {}  # 影片資訊
        video_dl_opts = {
            **self.ydl_opts,
            "outtmpl": {
                "default": str(tmp_dir / "%(format_id)s.%(ext)s"),
                "infojson": str(tmp_dir) + "/",
                "subtitle": str(tmp_dir) + "/",
            },  # 對命名的處理
        }

        # 下載
        with YoutubeDL(video_dl_opts) as ydl:  # pyright: ignore[reportArgumentType]
            try:
                logger.debug("下載影片")
                ydl.download(url)
            except DownloadError as e:
                self._error_message(e)
                return True

        # 獲取info資料
        with open(tmp_dir / ".info.json", encoding="utf-8") as f:
            video_info = json.load(f)

        # 下載縮圖
        logger.debug("下載縮圖")
        Path(tmp_dir / "cover.jpg").write_bytes(requests.get(video_info["thumbnail"]).content)
        return False

    def _error_message(self, e: DownloadError):
        for error, msg in self.error_dict.items():
            if error in str(e):
                logger.error(msg)
                time.sleep(2)
                break
        else:
            logger.error("未測試出的錯誤，請考慮將以下錯誤回報")
            logger.error(str(e))
            time.sleep(2)
