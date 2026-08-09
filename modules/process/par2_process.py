import logging
import subprocess

from . import file_operation
from .data_process import PostProcessData

logger = logging.getLogger(__name__)


def par2_create(data: PostProcessData, check_error: bool):
    """par2檔案處理模塊"""

    # 如果缺少par2直接跳出
    if "par2" in data.miss_program:
        return

    # 驗證par2回傳值
    if check_error:
        logger.error(f"影片：{data.video_info['title']}，檢查到par2檔案出現問題，建議重新下載檔案")
        return

    logger.debug("進入par2創建函式")

    # 先清除par2與舊留言
    for f in data.finish_dir.glob("*.par2"):
        f.unlink()
    file_operation.old_comment_clear(data)

    # par2參數設定
    # fmt: off
    par2_cmd = [
            "par2", "c",
            "-r30", "-b10000", "-n1",
            "check.par2",
        ]
    # fmt: on

    # 遞歸檔案清單
    par2_cmd += [f.name for f in data.finish_dir.iterdir()]

    # 校驗檔創建與驗證
    logger.debug(par2_cmd)
    subprocess.run(par2_cmd, capture_output=True, cwd=data.finish_dir)
    par2_verify = subprocess.run(
        ("par2", "v", "check.par2"), capture_output=True, text=True, cwd=data.finish_dir
    )
    if par2_verify.returncode != 0:
        for f in data.finish_dir.glob("*.par2"):
            f.unlink()
        logger.error(f"影片：{data.video_info['title']}，par2檔案未能成功創建，請嘗試手動創建")


def par2_verify(data: PostProcessData) -> bool:
    """檔案更新前驗證與修復"""

    # 如果不更新留言或缺少par2直接跳出
    if not data.comment_update or "par2" in data.miss_program:
        return False

    logger.debug("進入par校驗函式")

    par2_verify = subprocess.run(
        ("par2", "v", "check.par2"), capture_output=True, text=True, cwd=data.finish_dir
    )
    match par2_verify.returncode:
        # 清理檔案並繼續
        case 0:
            file_operation.old_comment_clear(data)
            return False
        # 嘗試修復並繼續
        case 1:
            par2_repair = subprocess.run(
                ("par2", "r", "check.par2"),
                capture_output=True,
                text=True,
                cwd=data.finish_dir,
            )
            if par2_repair.returncode != 0:
                logger.error(f"影片：{data.video_info['title']}，自動修復失敗，請嘗試重新下載")
                return True
            for f in data.finish_dir.glob("*.1"):
                f.unlink()
            file_operation.old_comment_clear(data)
            return False
        # 無法修復，跳過
        case 2:
            logger.error(f"影片：{data.video_info['title']}，檔案嚴重損毀，請嘗試重新下載")
            return True
        # 未知狀況
        case _:
            logger.error(f"於影片：{data.video_info['title']}，發現未測試出的錯誤")
            logger.error(par2_verify.stderr.strip())
            return True
