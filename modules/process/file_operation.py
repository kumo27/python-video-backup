from pathlib import Path

from aiopathlib import AsyncPath

from .data_process import PostProcessData


async def rename(tmp_dir: AsyncPath) -> None:
    for path in tmp_dir.iterdir():
        if await path.is_file() and path.name[0] == ".":
            await path.rename(path.with_name(path.name[1:]))


async def move(data: PostProcessData) -> None:
    """完成檔案移動"""
    for file_path in data.tmp_dir.iterdir():
        if file_path.suffix == ".mkv":
            Path(file_path).move(data.finish_dir / "video.mkv")
        elif file_path.suffix in (".srt", ".ass", ".vtt") or (
            await file_path.is_dir() and file_path.name == ".meta_data"
        ):
            Path(file_path).move_into(data.finish_dir)


def old_comment_clear(data: PostProcessData) -> None:
    comment_list = [f.name for f in data.finish_dir.glob("comment_*")]
    comment_list.sort(reverse=True)
    for f in data.finish_dir.glob("comment_*"):
        if f.name == comment_list[0]:
            continue
        f.unlink()
