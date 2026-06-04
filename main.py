import sys
import time
import logging
import process
import downloader
from pathlib import Path
from config import log_root
from config import temp_dir

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
    try:
        urls = urls_preprocess()
        ydl_opts = browser()
        for url in urls:
            if url.strip() == '': continue
            get_dict = downloader.download(url, ydl_opts)
            if get_dict is None:
                fail_urls_logger.error(url.strip())
                continue
            process.merge(get_dict['finish_dir'])
            process.json_process(get_dict['video_info'], get_dict['finish_dir'])
            process.par2_process(get_dict['finish_dir'])
            temp_init()
    except KeyboardInterrupt:
        temp_init()
        sys.exit()
    finally:
        temp_init()
        sys.exit()