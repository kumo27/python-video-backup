import json
import logging
from datetime import datetime
from pathlib import Path

from .data_process import PostProcessData

logger = logging.getLogger(__name__)


def comment_process(data: PostProcessData):
    """留言處理"""

    logger.debug("進入留言處理函式")

    # 變數定義
    output_comment: dict = {}  # 留言內文

    # 留言json處理與寫入
    output_comment = {
        f"第{i + 1}條留言": comment for i, comment in enumerate(data.video_info["comments"])
    }
    with open(
        (data.finish_dir / f"comment_{datetime.now():%Y%m%d%H%M}.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(output_comment, f, indent=4, ensure_ascii=False)


def info_process(data: PostProcessData):
    """影片資訊處理"""

    logger.debug("進入info處理函式")

    # 變數定義
    output_info: str = ""  # 影片資訊內文

    # 影片資訊處理
    output_info = (
        "標題:\n"
        f"{data.video_info['title']}\n"
        "\n"
        "發布日期:\n"
        f"{data.release_date:%Y/%m/%d}\n"
        "\n"
        "影片網址:\n"
        f"{data.video_info['webpage_url']}\n"
        "\n"
        "說明欄:\n"
        f"{data.video_info['description']}"
    )

    # 影片資訊寫入
    with open((data.finish_dir / "info.txt"), "w", encoding="utf-8") as f:
        f.write(output_info)


def live_chat_process(data: PostProcessData):
    """聊天室處理"""

    logger.debug("進入聊天室處理函式")

    # 如果沒有就跳出
    if not Path(data.tmp_dir / "live_chat.json").exists():
        return

    # 變數定義
    output_live_chat: dict = {}  # 聊天室內文

    # 聊天室json處理與寫入
    with open(data.tmp_dir / "live_chat.json", encoding="utf-8") as f:
        output_live_chat = {
            f"第{i + 1}條訊息": json.loads(live_chat) for i, live_chat in enumerate(f)
        }
    with open((data.finish_dir / "live_chat.json"), "w", encoding="utf-8") as f:
        json.dump(output_live_chat, f, indent=4, ensure_ascii=False)
