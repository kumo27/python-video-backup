import json
import logging
import re
from datetime import datetime
from typing import Any

import aiofiles

from .data_process import PostProcessData

logger = logging.getLogger(__name__)


def comment_author_thumbnail(data: PostProcessData) -> dict[str, str]:
    author_thumbnail_dict: dict[str, str] = {}

    for comments in data.video_info["comments"]:
        author_thumbnail_match = re.search(
            r"https://yt3.ggpht.com/[^=]+", comments["author_thumbnail"]
        )

        if author_thumbnail_match is None:
            logger.warning(
                f"留言者:{comments['author']}，頭貼無法下載，請考慮回報(取得url:{comments['author_thumbnail']})"
            )
            continue

        author_thumbnail_dict[comments["author"]] = author_thumbnail_match.group()

    return author_thumbnail_dict


async def comment_process(data: PostProcessData, name_suffix_dict: dict[str, str]) -> None:
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
        }

    # 資料處理
    for key, comments_data in data_dict.items():
        # 深度尋找
        depth = 0
        depth_key = key
        while (depth_key := parent_dict[depth_key]) != "root":
            depth += 1

        # 輸出格式化
        text: str = comments_data["text"]
        text = text.replace("\r", "")
        text = text.replace("\n", f"<br>\n{' ' * depth * 2}  > ")
        output_list.append(
            f'{" " * depth * 2}- <img src=".meta_data/{comments_data["author"]}.{name_suffix_dict[comments_data["author"]]}" width="40" height="40">'  # noqa: E501
            f"{comments_data['author']}_{comments_data['time']:%Y/%m/%d}\n"
            f"{' ' * depth * 2}  > {text}\n"
        )

    # 檔案寫入
    async with aiofiles.open(
        (data.finish_dir / f"comment_{datetime.now():%Y%m%d%H%M}.md"), mode="w", encoding="utf-8"
    ) as f:
        await f.write("".join(output_list))


async def info_process(data: PostProcessData) -> None:
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
    async with aiofiles.open((data.finish_dir / "info.txt"), "w", encoding="utf-8") as f:
        await f.write(output_info)


async def live_chat_process(data: PostProcessData) -> None:
    """聊天室處理"""

    logger.debug("進入聊天室處理函式")

    # 如果沒有就跳出
    if not await (data.tmp_dir / "live_chat.json").exists():
        return

    # 變數定義
    output_live_chat: dict = {}  # 聊天室內文

    # 聊天室json處理與寫入
    async with aiofiles.open(data.tmp_dir / "live_chat.json", encoding="utf-8") as f:
        i = 0
        while line := await f.readline():
            i += 1
            output_live_chat[f"第{i}條訊息"] = json.loads(line)

    async with aiofiles.open((data.finish_dir / "live_chat.json"), "w", encoding="utf-8") as f:
        await f.write(json.dumps(output_live_chat, indent=4, ensure_ascii=False))
