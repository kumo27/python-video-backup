import sys
import time
import logging
import downloader
from pathlib import Path
from config import log_root
from config import temp_dir
from process import PostProcess

#log檔案變數
log_dir: Path = Path.cwd() / 'log'

#主log初始化
log_dir.mkdir(exist_ok=True)
logger = logging.getLogger(log_root)
logger.setLevel(logging.DEBUG)

#控制台設定
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_fmt = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(console_fmt)
logger.addHandler(console_handler)

#log檔案設定
file_handler = logging.FileHandler((log_dir / 'full_log.log'), 'w', 'utf-8')
file_handler.setLevel(logging.DEBUG)
file_fmt = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
)
file_handler.setFormatter(file_fmt)
logger.addHandler(file_handler)

#失敗連結log初始化
fail_urls_logger = logging.getLogger('fail_urls')
fail_urls_logger.propagate = False
fail_urls_logger.setLevel(logging.DEBUG)

#失敗連結log檔案設定
file_handler = logging.FileHandler((log_dir / 'fail_urls.txt'),'w', 'utf-8')
file_handler.setLevel(logging.DEBUG)
file_fmt = logging.Formatter('%(message)s')
file_handler.setFormatter(file_fmt)
fail_urls_logger.addHandler(file_handler)

def temp_init():
    '''temp資料夾初始化'''
    if temp_dir.exists():
        for f in temp_dir.iterdir():
            f.unlink()
    temp_dir.mkdir(exist_ok=True)

def urls_preprocess() -> list[str]:
    '''影片連結預處理'''
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

def dl_opt_ask():
    '''下載選項的設定與詢問'''
    ydl_opts = {
        'format': 'bv,ba', #品質控制
        'format_sort': ['res','vcodec:avc+vp9'], #微調後的排序
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
            break
        else:
            print('\033c')
            print('輸入無效，請檢查輸入後再試一次')
            time.sleep(2)
    
    while True:
        ask_str = input('是否僅更新留言(y/n): ').strip().lower()
        if ask_str == 'y':
            ydl_opts['skip_download'] = True
            comment_update = True
            break
        elif ask_str == 'n':
            comment_update = False
            break
        print('\033c', end='')
        print('無效參數')
        time.sleep(1)
    
    return ydl_opts, comment_update

if __name__ == '__main__':
    try:
        urls = urls_preprocess()
        ydl_opts, comment_update = dl_opt_ask()
        for url in urls:
            if url.strip() == '': continue
            temp_init()
            get_dict = downloader.download(url, ydl_opts)
            if get_dict is None:
                fail_urls_logger.error(url.strip())
                continue
            process = PostProcess(temp_dir, get_dict['finish_dir'], comment_update)
            process.merge()
            check_error = process.par2_verify()
            process.json_process(get_dict['video_info'])
            process.par2_create(check_error)
    except KeyboardInterrupt:
        sys.exit()