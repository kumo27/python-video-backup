import asyncio

from modules.process.data_process import PostProcessData


async def cover_jxl_conversion(data: PostProcessData) -> None:
    """將封面壓縮成jxl"""

    # 如果缺失程式或無法壓縮提早退出
    if "cjxl" in data.miss_program or not await (data.tmp_dir / "cover.jpg").is_file():
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
