import sys
import time
import json
import requests
from pathlib import Path
from config import temp_dir
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

#下載
def download(urls) -> tuple[dict, Path]:
    #變數定義
    video_info = {} #影片資訊
    ydl_opts = {
        'format': 'bv,ba', #最佳品質
        'outtmpl': {
            'default': str(temp_dir) + '/%(format_id)s.%(ext)s', 
            'infojson': str(temp_dir) + '/', 
            'subtitle': str(temp_dir) + '/', 
            'description': str(temp_dir) + '/', 
        }, #對命名的處理
        'writeinfojson': True, #寫入影片資訊
        'getcomments': True, #寫入留言
        'writesubtitles': True, #寫入字幕
        'subtitleslangs': ['all'], #指定字幕範圍(全部，包含聊天室)
    } #下載選項
    browser_opt = ['不匯入', 'chrome', 'edge', 'brave', 'firefox'] #瀏覽器選項

    #生成詢問內容
    ask_str = '\033c' + '選擇是否從瀏覽器匯入cookie:\n'
    for i, browser in enumerate(browser_opt):
        ask_str += f'{i}: {browser}\n'
    ask_str += ': '

    #選擇從瀏覽器匯入cookie
    while True:
        browser_key = input(ask_str).strip()
        if browser_key.isdecimal() and int(browser_key) < len(browser_opt):
            if int(browser_key) > 0:
                ydl_opts['cookiesfrombrowser'] = (browser_opt[int(browser_key)], )
            print('\033c', end='')
            break
        else:
            print('\033c')
            print('輸入無效，請檢查輸入後再試一次')
            time.sleep(2)
            

    #下載
    with YoutubeDL(ydl_opts) as ydl: # pyright: ignore[reportArgumentType]
        try:
            ydl.download(urls)
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
