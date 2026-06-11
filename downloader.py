import json
import time
import logging
import requests
from pathlib import Path
from config import log_root
from config import temp_dir
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

logger = logging.getLogger(f'{log_root}.{__name__}')

#下載
def download(url, ydl_opts):
    #變數定義
    video_info = {} #影片資訊

    #下載
    with YoutubeDL(ydl_opts) as ydl: # pyright: ignore[reportArgumentType]
        print('\033c', end='')
        try:
            ydl.download(url)
        except DownloadError as e:
            #錯誤字典
            error_dict ={
                'Sign in to confirm you’re not a bot.': 'youtube要求登入，請考慮匯入瀏覽器cookie', 
                'HTTP Error 403: Forbidden': 'error 403，禁止訪問，如果先前未匯入cookie請嘗試匯入', 
                'Read timed out.': '網路連線逾時，請檢查網路後再試一次', 
                'Failed to resolve': '解析失敗，請檢查網路後再試一次', 
                'is not a valid URL': '無效連結，請檢查連結後再試一次', 
                'Connection reset by peer': 'error 104，連線被重置，請稍後重試'
            }

            for error, msg in error_dict.items():
                if error in str(e):
                    print()
                    logger.error(msg)
                    time.sleep(2)
                    break
            else:
                print()
                logger.error('未測試出的錯誤，請考慮將以下錯誤回報')
                logger.error('\n' + str(e))
                time.sleep(2)
            return None

    #重命名部份檔案
    for file_path in temp_dir.iterdir():
        if file_path.name[0] == '.':
            file_path.rename(file_path.with_name(file_path.name[1:]))


    #讀取影片資訊與創建完成資料夾
    with open(temp_dir / 'info.json') as f:
        video_info = json.load(f)
    clean_title = str.translate(video_info['title'], str.maketrans('/\\', '⧸⧹'))
    finish_dir: Path = Path.cwd() / 'download' / clean_title
    finish_dir.mkdir(parents = True, exist_ok = True)
    
    #下載縮圖
    Path.write_bytes((temp_dir / 'cover.jpg'), requests.get(video_info['thumbnail']).content)

    return {'video_info': video_info, 'finish_dir': finish_dir}
