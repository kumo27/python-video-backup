import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from sys import exit
from tempfile import TemporaryDirectory

from tqdm import tqdm

from modules.config import fail_urls_log_root, log_root, max_workers, temp_dir
from modules.downloader import DL
from modules.init import main_init
from modules.interactive import Interactive
from modules.process import PostProcess, PostProcessData, urls_preprocess

logger = logging.getLogger(log_root)
fail_urls_logger = logging.getLogger(fail_urls_log_root)


def main(url: str):
    if url.strip() == "":
        return

    # 下載
    tmp = TemporaryDirectory(dir=temp_dir)
    tmp_dir = Path(tmp.name)

    dl_error = dl.download(url, tmp_dir)
    if dl_error:
        fail_urls_logger.error(url.strip())
        tmp.cleanup()
        return

    # 後處理
    data = PostProcessData.data_process(tmp_dir, user_parameters.comment_update, miss_program)
    process = PostProcess(data)
    process.meta_clear()
    process.move()
    process.json_process()
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
            work = (executor.submit(main, url) for url in urls)
            for result in as_completed(work):
                # 後處理
                main_return = result.result()
                if main_return is not None:
                    process, tmp = main_return
                    process.jxl_conversion()
                    tmp.cleanup()
                    check_error = process.par2_verify()
                    process.par2_create(check_error)

                pbar.update(1)

    except KeyboardInterrupt:
        exit()
