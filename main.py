import asyncio
import json
import logging
from asyncio.locks import Semaphore
from asyncio.tasks import Task
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor

import aiofiles
from aiohttp import ClientSession
from aiopathlib import AsyncPath
from tqdm.asyncio import tqdm_asyncio

from modules.config import FAIL_URLS_LOG_ROOT, MAX_WORKERS
from modules.downloader import DL
from modules.env_init import main_init
from modules.interactive import Interactive
from modules.process import file_operation, meta_process, par2_process, post_process, video_process
from modules.process.data_process import PostProcessData
from modules.process.preprocess import urls_preprocess

logger = logging.getLogger("modules")
fail_urls_logger = logging.getLogger(FAIL_URLS_LOG_ROOT)


async def post_process_workflow(data: PostProcessData, session: ClientSession) -> None:
    # 隱藏文件重命名、完成資料夾創建
    post_env_init: tuple[Coroutine, ...] = (
        data.finish_dir.mkdir(parents=True, exist_ok=True),
        file_operation.rename(data.tmp_dir),
    )
    await asyncio.gather(*post_env_init)

    post_task: list[Task] = []

    if not (user_parameters.comment_update or "mkvpropedit" in MISS_PROGRAM):
        # 影片封裝內，詮釋資料清理
        post_task.append(asyncio.create_task(video_process.meta_clear(data)))

    # 詮釋資料處理(除留言)
    post_task.append(asyncio.create_task(meta_process.info_process(data)))
    post_task.append(asyncio.create_task(meta_process.live_chat_process(data)))

    # 留言頭貼下載
    make_meta_tmp_dir = asyncio.create_task(
        (data.tmp_dir / ".meta_data").mkdir()
    )  # 創建詮釋資料暫存資料夾
    author_thumbnail_dict = meta_process.comment_author_thumbnail(data)  # 獲取名稱與url字典
    await make_meta_tmp_dir  # 確保暫存資料夾已創建
    dl_author_thumbnail_task = [
        asyncio.create_task(dl.author_thumbnail_get(session, name_and_url, data.tmp_dir))
        for name_and_url in author_thumbnail_dict.items()
    ]  # 創建下載任務
    name_suffix_dict = {}
    for task_return in asyncio.as_completed(dl_author_thumbnail_task):
        update_dict = await task_return
        name_suffix_dict.update(update_dict)

    # 留言markdown創建
    post_task.append(asyncio.create_task(meta_process.comment_process(data, name_suffix_dict)))

    # 搬移處理完成的資料
    await asyncio.gather(*post_task)


async def main_workflow(url: str, executor: ThreadPoolExecutor, session: ClientSession) -> None:
    """主下載工作流"""
    loop = asyncio.get_running_loop()

    async with tmp_semaphore, aiofiles.tempfile.TemporaryDirectory(prefix="python_backup_") as tmp:
        # 創建詮釋資料暫存資料夾
        tmp_path: AsyncPath = AsyncPath(tmp)

        # 影片下載
        dl_error = await loop.run_in_executor(executor, dl.download, url, tmp_path)
        if dl_error:
            fail_urls_logger.error(url.strip())
            return

        # 影片資訊讀取
        async with aiofiles.open(tmp_path / ".info.json", encoding="utf-8") as f:
            info_str = await f.read()
        video_info: dict = json.loads(info_str)

        # 縮圖下載
        dl_error = await dl.cover_get(session, video_info["thumbnail"], tmp_path)
        if dl_error:
            fail_urls_logger.error(url.strip())
            return

        # 後處理資料創建
        data = PostProcessData.data_process(video_info, tmp_path)

        # 後處理
        await post_process_workflow(data, session)

        # 封面圖壓縮
        if not (
            "cjxl" in MISS_PROGRAM  # 缺少程式
            or not await (tmp_path / "cover.jpg").is_file()  # 檔案不存在，或非jpg
            or user_parameters.comment_update  # 僅更新留言
        ):
            await post_process.cover_jxl_conversion(data)

        # breakpoint()

        # 完成檔案移動
        await file_operation.move(data)

    # par2創建
    async with par2_semaphore:
        if "par2" in MISS_PROGRAM:
            return

        check_error: bool = False
        if user_parameters.comment_update:
            check_error = await par2_process.par2_verify(data)

        await par2_process.par2_create(data, check_error)


async def start_workflow(urls: tuple[str, ...]) -> None:
    """啟動下載工作流"""
    async with ClientSession() as session:
        with ThreadPoolExecutor(MAX_WORKERS) as executor:
            tasks = [asyncio.create_task(main_workflow(url, executor, session)) for url in urls]

            await tqdm_asyncio.gather(
                *tasks,
                desc="所有影片下載中",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
            )


if __name__ == "__main__":
    # 初始化
    MISS_PROGRAM: frozenset[str] = main_init()
    user_parameters: Interactive = Interactive()
    user_parameters.main_ask()
    # 連結預處理
    dl: DL = DL(user_parameters.ydl_update_opts)
    urls: tuple[str, ...] = urls_preprocess(user_parameters.urls, dl)

    # 限制任務數
    par2_semaphore: Semaphore = asyncio.Semaphore(1)
    tmp_semaphore: Semaphore = asyncio.Semaphore(10)
    asyncio.run(start_workflow(urls))
