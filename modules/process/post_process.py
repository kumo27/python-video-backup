import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from .data_process import PostProcessData
from .file_operation import move
from .meta_process import comment_process, info_process, live_chat_process
from .par2_process import par2_create, par2_verify
from .video_process import meta_clear


class PostProcess:
    """後處理模塊"""

    def __init__(self, data: PostProcessData) -> None:
        # 變數定義
        self.data = data

        self._env_init()

    def _env_init(self):
        # 重命名
        for file_path in self.data.tmp_dir.iterdir():
            if file_path.name[0] == ".":
                file_path.rename(file_path.with_name(file_path.name[1:]))

        self.data.finish_dir.mkdir(parents=True, exist_ok=True)

    def in_async(self):
        meta_clear(self.data)
        info_process(self.data)
        comment_process(self.data)
        live_chat_process(self.data)
        move(self.data)

    def not_in_async(self, tmp: TemporaryDirectory):
        self._cover_jxl_conversion()
        tmp.cleanup()
        check_error = par2_verify(self.data)
        par2_create(self.data, check_error)

    def _cover_jxl_conversion(self):
        """將封面壓縮成jxl"""

        if "cjxl" in self.data.miss_program:
            Path(self.data.tmp_dir / "cover.jpg").move_into(self.data.finish_dir)
            return

        # fmt: off
        jxl_cmd = (
            "cjxl",
            (self.data.tmp_dir / "cover.jpg"),
            (self.data.finish_dir / "cover.jxl"),
            "-e", "9",
            "--brotli_effort", "11",
        )
        # fmt: on
        subprocess.run(jxl_cmd, capture_output=True)
