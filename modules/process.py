import json
import logging
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from .config import download_dir, fail_urls_log_root, log_root, max_workers
from .downloader import DL

logger = logging.getLogger(f"{log_root}.{__name__}")
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


@dataclass(frozen=True, slots=True)
class PostProcessData:
    tmp_dir: Path
    comment_update: bool
    miss_program: tuple[str, ...]
    video_info: dict
    finish_dir: Path

    @classmethod
    def data_process(
        cls,
        tmp_dir: Path,
        comment_update: bool,
        miss_program: tuple[str, ...],
        finish_dir: Path | None = None,
    ):
        # 取得影片資料
        with open(tmp_dir / ".info.json", encoding="utf-8") as f:
            video_info: dict = json.load(f)

        # 對預設值的處理
        if finish_dir is None:
            # 路徑合法化
            clean_title = str.translate(video_info["title"], str.maketrans("/\\", "⧸⧹"))
            clean_channel = str.translate(video_info["channel"], str.maketrans("/\\", "⧸⧹"))
            release_date = video_info.get("release_date") or video_info.get("upload_date")
            # 合成完成資料夾
            finish_dir = (
                download_dir / clean_channel / (f"{release_date}_{clean_title}_{video_info['id']}")
            )

        return cls(tmp_dir, comment_update, miss_program, video_info, finish_dir)


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

    def meta_clear(self):
        """影片、音訊與字幕合併，並包含元數據清理"""
        # 如果僅更新留言就跳出
        if self.data.comment_update or "mkvpropedit" in self.data.miss_program:
            return

        logger.debug("進入清理函式")

        # 影片元數據清理
        # fmt: off
        meta_clear_cmd = (
            "mkvpropedit", (self.data.finish_dir / "video.mkv"),
            "--delete-track-statistics-tags",
            "--edit", "info",
            "--delete", "date",
            "--delete", "title",
            "--tags", "all:",
            "--set", "writing-application=",
            "--set", "muxing-application=",
        )
        # fmt: on
        subprocess.run(meta_clear_cmd, capture_output=True)

    def move(self):
        for file_path in self.data.tmp_dir.iterdir():
            if file_path.suffix == ".mkv":
                file_path.move(self.data.finish_dir / "video.mkv")
            elif file_path.suffix in (".srt", ".ass", ".vtt"):
                file_path.move_into(self.data.finish_dir)

    def jxl_conversion(self):
        if "cjxl" not in self.data.miss_program:
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
        else:
            Path(self.data.tmp_dir / "cover.jpg").move_into(self.data.finish_dir)

    def json_process(self):
        """元數據json的處理模塊"""

        logger.debug("進入json處理函式")

        # 變數定義
        output_comment: dict = {}  # 留言內文
        output_live_chat: dict = {}  # 聊天室內文
        output_info: str = ""  # 影片資訊內文

        # 留言json處理與寫入
        output_comment = {
            f"第{i + 1}條留言": comment
            for i, comment in enumerate(self.data.video_info["comments"])
        }
        with open(
            (self.data.finish_dir / f"comment_{datetime.now():%Y%m%d%H%M}.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(output_comment, f, indent=4, ensure_ascii=False)

        # 如果僅更新留言就跳出
        if self.data.comment_update:
            return

        # 獲取發布或上傳日期
        date_input = self.data.video_info.get("release_date") or self.data.video_info.get(
            "upload_date"
        )
        release_date = datetime.strptime(date_input, "%Y%m%d").strftime("%Y/%m/%d")  # pyright: ignore[reportArgumentType]

        # 影片資訊處理
        output_info = (
            "標題:\n"
            f"{self.data.video_info['title']}\n"
            "\n"
            "發布日期:\n"
            f"{release_date}\n"
            "\n"
            "影片網址:\n"
            f"{self.data.video_info['webpage_url']}\n"
            "\n"
            "說明欄:\n"
            f"{self.data.video_info['description']}"
        )

        # 影片資訊寫入
        with open((self.data.finish_dir / "info.txt"), "w", encoding="utf-8") as f:
            f.write(output_info)

        # 聊天室json處理與寫入
        if Path(self.data.tmp_dir / "live_chat.json").exists():
            with open(self.data.tmp_dir / "live_chat.json", encoding="utf-8") as f:
                output_live_chat = {
                    f"第{i + 1}條訊息": json.loads(live_chat) for i, live_chat in enumerate(f)
                }
            with open((self.data.finish_dir / "live_chat.json"), "w", encoding="utf-8") as f:
                json.dump(output_live_chat, f, indent=4, ensure_ascii=False)

    def par2_create(self, check_error: bool):
        """par2檔案處理模塊"""

        # 如果缺少par2直接跳出
        if "par2" in self.data.miss_program:
            return

        # 檢查par2驗證回傳值
        if check_error:
            logger.error(
                f"影片：{self.data.video_info['title']}，檢查到par2檔案出現問題，建議重新下載檔案"
            )
            return

        logger.debug("進入par2創建函式")

        # 先清除par2與舊留言
        for f in self.data.finish_dir.glob("*.par2"):
            f.unlink()
        self._old_comment_clear()

        # par2參數設定
        # fmt: off
        par2_cmd = [
            "par2", "c",
            "-r30", "-b10000", "-n1",
            "check.par2",
        ]
        # fmt: on

        # 遞歸檔案清單
        par2_cmd += [f.name for f in self.data.finish_dir.iterdir()]

        # 校驗檔創建與驗證
        logger.debug(par2_cmd)
        subprocess.run(par2_cmd, capture_output=True, cwd=self.data.finish_dir)
        par2_verify = subprocess.run(
            ("par2", "v", "check.par2"), capture_output=True, text=True, cwd=self.data.finish_dir
        )
        if par2_verify.returncode != 0:
            for f in self.data.finish_dir.glob("*.par2"):
                f.unlink()
            logger.error(
                f"影片：{self.data.video_info['title']}，par2檔案未能成功創建，請嘗試手動創建"
            )

    def par2_verify(self) -> bool:
        """檔案更新前驗證與修復"""
        # 如果不更新留言或缺少par2直接跳出
        if not self.data.comment_update or "par2" in self.data.miss_program:
            return False

        logger.debug("進入par校驗函式")

        par2_verify = subprocess.run(
            ("par2", "v", "check.par2"), capture_output=True, text=True, cwd=self.data.finish_dir
        )
        match par2_verify.returncode:
            # 清理檔案並繼續
            case 0:
                self._old_comment_clear()
                return False
            # 嘗試修復並繼續
            case 1:
                par2_repair = subprocess.run(
                    ("par2", "r", "check.par2"),
                    capture_output=True,
                    text=True,
                    cwd=self.data.finish_dir,
                )
                if par2_repair.returncode != 0:
                    logger.error(
                        f"影片：{self.data.video_info['title']}，自動修復失敗，請嘗試重新下載"
                    )
                    return True
                for f in self.data.finish_dir.glob("*.1"):
                    f.unlink()
                self._old_comment_clear()
                return False
            # 無法修復，跳過
            case 2:
                logger.error(f"影片：{self.data.video_info['title']}，檔案嚴重損毀，請嘗試重新下載")
                return True
            # 未知狀況
            case _:
                logger.error(f"於影片：{self.data.video_info['title']}，發現未測試出的錯誤")
                logger.error(par2_verify.stderr.strip())
                return True

    def _old_comment_clear(self):
        comment_list = [f.name for f in self.data.finish_dir.glob("comment_*")]
        comment_list.sort(reverse=True)
        for f in self.data.finish_dir.glob("comment_*"):
            if f.name == comment_list[0]:
                continue
            f.unlink()
