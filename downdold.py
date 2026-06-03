import sys
import time
import json
import requests
from pathlib import Path
from config import temp_dir
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

#下載
def download(url, ydl_opts) -> tuple[dict, Path]:
    #變數定義
    video_info = {} #影片資訊

    #下載
    with YoutubeDL(ydl_opts) as ydl: # pyright: ignore[reportArgumentType]
        try:
            ydl.download(url)
        except DownloadError as e:
            if 'Sign in to confirm you’re not a bot.' in str(e):
                print('\nyoutube要求登入，請考慮匯入瀏覽器cookie')
                sys.exit()
            elif 'Read timed out.' in str(e):
                print('\n網路連線逾時，請檢查網路後再試一次')
                sys.exit()
            elif 'Unable to download API page' in str(e):
                print('\nAPI解析失敗，請檢查網路後再試一次')
                sys.exit()
            elif 'is not a valid URL' in str(e):
                print('\n無效連結，請檢查連結後再試一次')
                sys.exit()
            else:
                print('\n意外錯誤，請考慮將以下錯誤回報\n' + str(e))
                sys.exit()

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

    return video_info, finish_dir
