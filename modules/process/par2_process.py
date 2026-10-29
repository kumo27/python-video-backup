import asyncio
import logging

from .data_process import PostProcessData

logger = logging.getLogger(__name__)


async def par2_create(data: PostProcessData, check_error: bool) -> None:
    """par2檔案處理模塊"""

    logger.debug("進入par2創建函式")

    # 先清除par2與舊留言
    for f in data.finish_dir.glob("*.par2"):
        f.unlink()

    # par2參數設定
    # fmt: off
    par2_cmd = (
        "par2", "c",
        "-R", "-r30", "-b10000", "-n1",
        "check.par2", ".",
    )
    # fmt: on

    # 校驗檔創建
    logger.debug(par2_cmd)
    par2_create_process = await asyncio.create_subprocess_exec(
        *par2_cmd,
        cwd=data.finish_dir,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await par2_create_process.wait()

    # 校驗檔驗證
    par2_verify_process = await asyncio.create_subprocess_exec(
        *("par2", "v", "check.par2"),
        cwd=data.finish_dir,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    if await par2_verify_process.wait() != 0:
        for f in data.finish_dir.glob("*.par2"):
            f.unlink()
        logger.error(f"影片：{data.video_info['title']}，par2檔案未能成功創建，請嘗試手動創建")


async def par2_verify(data: PostProcessData) -> bool:
    """檔案更新前驗證與修復"""

    logger.debug("進入par校驗函式")

    par2_verify_process = await asyncio.create_subprocess_exec(
        *("par2", "v", "check.par2"),
        cwd=data.finish_dir,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )

    _stdout, stderr = await par2_verify_process.communicate()

    match await par2_verify_process.wait():
        # 清理檔案並繼續
        case 0:
            return False

        # 嘗試修復並繼續
        case 1:
            par2_repair_process = await asyncio.create_subprocess_exec(
                *("par2", "r", "check.par2"),
                cwd=data.finish_dir,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            if await par2_repair_process.wait() != 0:
                logger.error(f"影片：{data.video_info['title']}，自動修復失敗，請嘗試重新下載")
                return True
            for f in data.finish_dir.glob("*.1"):
                f.unlink()

            return False

        # 無法修復，跳過
        case 2:
            logger.error(f"影片：{data.video_info['title']}，檔案嚴重損毀，請嘗試重新下載")
            return True

        # 未知狀況
        case _:
            logger.error(f"於影片：{data.video_info['title']}，發現未測試出的錯誤")
            logger.error(stderr.decode().strip())
            return True
