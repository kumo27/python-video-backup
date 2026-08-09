from .data_process import PostProcessData


def move(data: PostProcessData):
    """完成檔案移動"""
    for file_path in data.tmp_dir.iterdir():
        if file_path.suffix == ".mkv":
            file_path.move(data.finish_dir / "video.mkv")
        elif file_path.suffix in (".srt", ".ass", ".vtt"):
            file_path.move_into(data.finish_dir)


def old_comment_clear(data: PostProcessData):
    comment_list = [f.name for f in data.finish_dir.glob("comment_*")]
    comment_list.sort(reverse=True)
    for f in data.finish_dir.glob("comment_*"):
        if f.name == comment_list[0]:
            continue
        f.unlink()
