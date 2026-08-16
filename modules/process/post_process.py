import asyncio
from pathlib import Path

from modules.process.data_process import PostProcessData


async def cover_jxl_conversion(data: PostProcessData) -> None:
    """將封面壓縮成jxl"""

    if "cjxl" in data.miss_program:
        Path(data.tmp_dir / "cover.jpg").move_into(data.finish_dir)
        return

    # fmt: off
    jxl_cmd = (
        "cjxl",
        (data.tmp_dir / "cover.jpg"),
        (data.finish_dir / "cover.jxl"),
        "-e", "9",
        "--brotli_effort", "11",
    )
    # fmt: on

    jxl_conversion_process = await asyncio.create_subprocess_exec(
        *jxl_cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await jxl_conversion_process.wait()
