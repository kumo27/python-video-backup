import logging
import subprocess

from ..config import log_root
from .data_process import PostProcessData

logger = logging.getLogger(f"{log_root}.{__name__}")


def meta_clear(data: PostProcessData):
    """影片封裝內元數據清理"""
    # 如果僅更新留言就跳出
    if data.comment_update or "mkvpropedit" in data.miss_program:
        return

    logger.debug("進入影片封裝內元數據清理函式")

    # 影片元數據清理
    # fmt: off
    meta_clear_cmd = (
        "mkvpropedit", (data.tmp_dir / "video.mkv"),
        "--delete-track-statistics-tags",
        "--edit", "info",
        "--delete", "date",
        "--delete", "title",
        "--tags", "all:",
        "--set", "writing-application=",
        "--set", "muxing-application=",
    )
    # fmt: on

    subprocess.run(meta_clear_cmd, capture_output=True)
