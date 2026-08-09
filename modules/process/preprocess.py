import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from ..config import fail_urls_log_root, max_workers
from ..downloader import DL

logger = logging.getLogger(__name__)
fail_urls_logger = logging.getLogger(fail_urls_log_root)


def urls_preprocess(urls: list[str], dl: DL) -> tuple[str, ...]:
    """影片連結預處理"""
    playlist_urls, video_urls = urls_classification(urls)
    playlist_video_list = get_playlist_video_urls(playlist_urls, dl)

    video_urls += playlist_video_list
    return tuple(dict.fromkeys(video_urls))


def urls_classification(urls: list[str]):
    """url分類"""
    # 變數定義
    playlist_urls: list[str] = []  # 播放清單
    video_urls: list[str] = []  # 一般影片

    # 分離播放清單或頻道網址
    for url in urls:
        # 空字串跳出
        if url.strip() == "":
            continue

        # 播放清單或頻道網址
        re_return = re.search(
            (
                r"youtube.com/playlist\?list=PL[\w-]{32}"
                r"|"
                r"youtube.com/@[^/]+"
                r"|"
                r"youtube.com/channel/UC[\w-]{22}"
            ),
            url,
        )
        if re_return is not None:
            playlist_urls.append("https://" + re_return.group())
            continue

        # 一般影片
        re_return = re.search(
            (
                r"youtube.com/watch\?v=[\w-]{11}"
                r"|"
                r"youtu.be/[\w-]{11}"
                r"|"
                r"youtube.com/shorts/[\w-]{11}"
            ),
            url,
        )
        if re_return is not None:
            video_urls.append("https://" + re_return.group())
            continue

        # 例外
        logger.error(f"程式目前可能無法下載「 {url.strip()} 」，請考慮將網址回報，非常抱歉")
        fail_urls_logger.error(url.strip())
    return playlist_urls, video_urls


def get_playlist_video_urls(playlist_urls: list[str], dl: DL):
    """獲取播放清單內的影片連結"""
    # 變數定義
    finish_urls: list[str] = []  # 回傳連結

    print()  # 終端排版

    # 多執行緒獲取播放清單內影片
    new_urls: dict[str, tuple[str, ...] | None] = {}
    with (
        tqdm(total=len(playlist_urls), leave=False, desc="播放清單轉換中") as pbar,
        ThreadPoolExecutor(max_workers) as executor,
    ):
        work = {executor.submit(dl.get_playlist_url, url): url for url in playlist_urls}
        for result in as_completed(work):
            url = work[result]
            new_urls[url] = result.result()
            pbar.update(1)

    # 處理獲取失敗的播放清單
    for url, video_id in new_urls.items():
        if video_id is None:
            fail_urls_logger.error(url)
            continue
        finish_urls += video_id

    return finish_urls
