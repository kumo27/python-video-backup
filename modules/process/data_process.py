import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..config import download_dir


@dataclass(frozen=True, slots=True)
class PostProcessData:
    release_date: datetime
    video_info: dict
    tmp_dir: Path
    finish_dir: Path
    comment_update: bool
    miss_program: tuple[str, ...]

    @classmethod
    def data_process(
        cls,
        comment_update: bool,
        miss_program: tuple[str, ...],
        tmp_dir: Path,
        finish_dir: Path | None = None,
    ):
        # 取得影片資料
        with open(tmp_dir / ".info.json", encoding="utf-8") as f:
            video_info: dict = json.load(f)

        # 影片發布日期
        video_date: str = video_info.get("release_date") or video_info.get("upload_date")  # pyright: ignore[reportAssignmentType]
        release_date: datetime = datetime.strptime(video_date, "%Y%m%d")

        # 對預設值的處理
        if finish_dir is None:
            # 路徑合法化
            clean_title = str.translate(video_info["title"], str.maketrans("/\\", "⧸⧹"))
            clean_channel = str.translate(video_info["channel"], str.maketrans("/\\", "⧸⧹"))

            # 合成完成資料夾
            finish_dir = (
                download_dir
                / clean_channel
                / (f"{release_date:%Y%m%d}_{clean_title}_{video_info['id']}")
            )

        return cls(release_date, video_info, tmp_dir, finish_dir, comment_update, miss_program)
