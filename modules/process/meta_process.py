import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..downloader import DL
from .data_process import PostProcessData

logger = logging.getLogger(__name__)


def comment_process(data: PostProcessData, tmp: Path):
    """留言處理"""

    logger.debug("進入留言處理函式")

    # 變數初始化
    parent_dict: dict[str, str] = {}  # 父級查找字典
    data_dict: dict[str, dict[str, Any]] = {}  # 資料字典
    output_list: list[str] = []  # 輸出文字

    # 字典創建
    for comments in data.video_info["comments"]:
        parent_dict[comments["id"]] = comments["parent"]
        data_dict[comments["id"]] = {
            "author": comments["author"],
            "text": comments["text"],
            "time": datetime.fromtimestamp(comments["timestamp"]),
            "author_thumbnail": re.search(
                r"https://yt3.ggpht.com/[^=]+", comments["author_thumbnail"]
            ).group(),
        }

    dl = DL({})
    # 資料處理
    for key, comments_data in data_dict.items():
        # 深度尋找
        depth = 0
        depth_key = key
        while (depth_key := parent_dict[depth_key]) != "root":
            depth += 1

        suffix = dl.author_thumbnail(
            comments_data["author"], comments_data["author_thumbnail"], tmp
        )
        # 輸出格式化
        text: str = comments_data["text"]
        text = text.replace("\r", "")
        text = text.replace("\n", f"<br>\n{' ' * depth * 2}  > ")
        output_list.append(
            f'{" " * depth * 2}- <img src=".meta_data/{comments_data["author"]}.{suffix}" width="40" height="40">{comments_data["author"]}_{comments_data["time"]:%Y/%m/%d}\n'
            f"{' ' * depth * 2}  > {text}\n"
        )

    # 檔案寫入
    with open(
        (data.finish_dir / f"comment_{datetime.now():%Y%m%d%H%M}.md"), mode="w", encoding="utf-8"
    ) as f:
        f.write("".join(output_list))


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
