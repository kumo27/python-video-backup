import asyncio
import logging

from .data_process import PostProcessData

logger = logging.getLogger(__name__)


async def meta_clear(data: PostProcessData) -> None:
    """影片封裝內詮釋資料清理"""

    # 如果僅更新留言就跳出
    if data.comment_update or "mkvpropedit" in data.miss_program:
        return

    logger.debug("進入影片封裝內詮釋資料清理函式")

    # 影片詮釋資料清理
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

    await asyncio.create_subprocess_exec(
        *meta_clear_cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
