import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from sys import exit
from tempfile import TemporaryDirectory

from tqdm import tqdm

from modules.config import fail_urls_log_root, max_workers
from modules.downloader import DL
from modules.init import main_init
from modules.interactive import Interactive
from modules.process.data_process import PostProcessData
from modules.process.post_process import PostProcess
from modules.process.preprocess import urls_preprocess

logger = logging.getLogger("modules")
fail_urls_logger = logging.getLogger(fail_urls_log_root)


def dl_workflow(tmp_path: Path, url: str):
    # 下載
    dl_error = dl.download(url, tmp_path)

    return dl_error


def io_intensive_preprocess_workflow(tmp_path: Path):
    data = PostProcessData.data_process(user_parameters.comment_update, miss_program, tmp_path)
    process = PostProcess(data)
    process.meta_process_and_clean(tmp_path)

    return process


def main_workflow(url: str):
    # 暫存區創建
    tmp = TemporaryDirectory(prefix="python_backup_")
    tmp_path = Path(tmp.name)
    (tmp_path / ".meta_data").mkdir(exist_ok=True)

    dl_error = dl_workflow(tmp_path, url)

    if dl_error:
        fail_urls_logger.error(url.strip())
        tmp.cleanup()
        return

    process = io_intensive_preprocess_workflow(tmp_path)

    return process, tmp


if __name__ == "__main__":
    try:
        # 預處理
        miss_program = main_init()
        user_parameters = Interactive()
        user_parameters.main_ask()
        dl = DL(user_parameters.ydl_update_opts)
        urls = urls_preprocess(user_parameters.urls, dl)

        with (
            tqdm(
                total=len(urls),
                desc="所有影片下載中",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
            ) as pbar,
            ThreadPoolExecutor(max_workers) as executor,
        ):
            work = (executor.submit(main_workflow, url) for url in urls)
            for result in as_completed(work):
                # 後處理
                main_return = result.result()

                if main_return is not None:
                    process, tmp = main_return
                    process.compress_verify(tmp)

                pbar.update(1)

    except KeyboardInterrupt:
        exit()
