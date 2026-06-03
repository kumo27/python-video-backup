import sys
import time
import process
import downdold
from pathlib import Path
from config import temp_dir

#初始化
def temp_init():
    if temp_dir.exists():
        for f in temp_dir.iterdir():
            f.unlink()
    temp_dir.mkdir(exist_ok=True)

#連結處理
def urls_preprocess() -> list[str] | str:
    #變數定義
    urls_txt = Path.cwd() / 'urls.txt'

    if urls_txt.is_file():
        while True:
            ask_str = input('是否使用urls.txt(y/n): ').strip().lower()
            if ask_str == 'y':
                urls = urls_txt.open().readlines()
                return urls
            elif ask_str == 'n':
                break
            print('\033c', end='')
            print('無效參數')
            time.sleep(1)

    urls = [input('請輸入影片網址: ')]
    return urls

#瀏覽器ckookie處理
def browser():
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
    
    return ydl_opts

if __name__ == '__main__':
    temp_init()
    urls = urls_preprocess()
    ydl_opts = browser()
    for url in urls:
        try:
            video_info, finish_dir = downdold.download(url, ydl_opts)
            process.merge(finish_dir)
            process.json_process(video_info, finish_dir)
            process.par2_process(finish_dir)
        except KeyboardInterrupt:
            sys.exit('\n')
        finally:
            temp_init()