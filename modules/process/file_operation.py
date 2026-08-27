import asyncio
from collections.abc import Coroutine

import aioshutil
from aiopathlib import AsyncPath

from .data_process import PostProcessData


async def rename(tmp_dir: AsyncPath) -> None:
    task_list: list[Coroutine] = [
        path.rename(path.with_name(path.name[1:]))
        for path in tmp_dir.iterdir()
        if await path.is_file() and path.name[0] == "."
    ]

    await asyncio.gather(*task_list)


async def move(data: PostProcessData) -> None:
    """完成檔案移動"""
    unlink_task_list: list[Coroutine] = []
    move_task_list: list[Coroutine] = []

    for file_path in data.tmp_dir.iterdir():
        # 影片本體移動
        if file_path.suffix == ".mkv":
            unlink_task_list.append((data.finish_dir / "video.mkv").unlink(missing_ok=True))
            move_task_list.append(aioshutil.move(file_path, data.finish_dir / "video.mkv"))
        # 字幕移動與封面移動
        elif file_path.suffix in (".srt", ".ass", ".vtt") or file_path.stem == "cover":
            unlink_task_list.append((data.finish_dir / file_path.name).unlink(missing_ok=True))
            move_task_list.append(aioshutil.move(file_path, data.finish_dir))
        # 詮釋資料移動
        elif await file_path.is_dir() and file_path.name == ".meta_data":
            if await (data.finish_dir / ".meta_data").is_dir():
                unlink_task_list.append(aioshutil.rmtree(data.finish_dir / ".meta_data"))

            move_task_list.append(aioshutil.move(file_path, data.finish_dir))

    await asyncio.gather(*unlink_task_list)
    await asyncio.gather(*move_task_list)


def old_comment_clear(data: PostProcessData) -> None:
    comment_list = [f.name for f in data.finish_dir.glob("comment_*")]
    comment_list.sort(reverse=True)
    for f in data.finish_dir.glob("comment_*"):
        if f.name == comment_list[0]:
            continue
        f.unlink()
