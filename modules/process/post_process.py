import asyncio

from modules.process.data_process import PostProcessData


async def cover_jxl_conversion(data: PostProcessData) -> None:
    """將封面壓縮成jxl"""

    # 提早退出
    if (
        "cjxl" in data.miss_program  # 缺少程式
        or not await (data.tmp_dir / "cover.jpg").is_file()  # 檔案不存在，或非jpg
        or data.comment_update  # 僅更新留言
    ):
        return

    # fmt: off
    jxl_cmd = (
        "cjxl",
        "cover.jpg",
        "cover.jxl",
        "-e", "9",
        "--brotli_effort", "11",
    )
    # fmt: on

    jxl_conversion_process = await asyncio.create_subprocess_exec(
        *jxl_cmd,
        cwd=data.tmp_dir,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    # 檢查結束碼
    if await jxl_conversion_process.wait() == 0:
        await (data.tmp_dir / "cover.jpg").unlink()
