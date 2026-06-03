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

    urls = input('請輸入影片網址: ')
    return urls

if __name__ == '__main__':
    temp_init()
    try:
        urls = urls_preprocess()
        video_info, finish_dir = downdold.download(urls)
        process.merge(finish_dir)
        process.json_process(video_info, finish_dir)
        process.par2_process(finish_dir)
    except KeyboardInterrupt:
        sys.exit('\n')
    finally:
        temp_init()