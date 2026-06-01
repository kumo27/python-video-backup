import sys
import json
import requests
import subprocess
from ffmpy import FFmpeg
from pathlib import Path
from datetime import date
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

#全域變數
temp_dir: Path = Path.cwd() / 'temp' #緩存目錄

#初始化
def temp_init():
    if temp_dir.exists():
        for f in temp_dir.iterdir():
            f.unlink()
    temp_dir.mkdir(exist_ok=True)

def urls_preprocess() -> list[str] | str:
    #變數定義
    urls_txt = Path.cwd() / 'urls.txt'

    if urls_txt.exists():
        ask_str = input('是否使用urls.txt(y/n): ').strip().lower()
        if ask_str == 'y':
            urls = urls_txt.open().readlines()
            return urls
        elif ask_str != 'n':
            print('\n無效參數')
            sys.exit()
    
    urls = input('\n請輸入影片網址: ')
    return urls

#下載
def download(urls) -> tuple[dict, Path]:
    #變數定義
    video_info = {} #影片資訊
    ydl_opts = {
        'format': 'bv,ba', #最佳品質
        'outtmpl': {
            'default': './temp/%(format_id)s.%(ext)s', 
            'infojson': './temp/', 
            'subtitle': './temp/', 
            'description': './temp/', 
        }, #對命名的處理
        'writeinfojson': True, #寫入影片資訊
        'getcomments': True, #寫入留言
        'writesubtitles': True, #寫入字幕
        'subtitleslangs': ['all'], #指定字幕範圍(全部，包含聊天室)
    } #下載選項
    browser_opt = ['不匯入', 'chrome', 'edge', 'brave', 'firefox'] #瀏覽器選項

    #生成詢問內容
    ask_str = '選擇是否從瀏覽器匯入cookie:\n'
    for i, browser in enumerate(browser_opt):
        ask_str += f'{i}: {browser}\n'
    ask_str += ': '

    #選擇從瀏覽器匯入cookie
    browser_key = input(ask_str).strip()
    if browser_key.isdecimal() and int(browser_key) < len(browser_opt):
        if int(browser_key) > 0:
            ydl_opts['cookiesfrombrowser'] = (browser_opt[int(browser_key)], )
    else:
        print('輸入無效，請檢查輸入後再試一次')
        sys.exit()

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

#合併
def merge(finish_dir: Path):
    #變數定義
    input_video_file: dict[Path, None] = {} #輸入ffmpeg的檔案
    ffmpeg_options: list = [] #ffmpeg的輸出參數
    
    #合併影片與字幕
    for file_path in temp_dir.iterdir():
        if file_path.suffix not in ['.json', '.jpg', '.txt']:
            input_video_file[file_path] = None
        else:
            continue

    #處理ffmpeg map
    for i in range(0, len(input_video_file)):
        ffmpeg_options += ['-map', str(i)]

    #ffmpeg輸出參數合併
    ffmpeg_options += [
        '-attach', (temp_dir / 'cover.jpg'), '-metadata:s:t', 'mimetype=image/jpeg', 
        '-c', 'copy', 
        '-loglevel', 'warning', '-hide_banner', '-stats'
    ]

    #影片元數據清理參數
    meta_clear_options = [
        'mkvpropedit', (finish_dir / 'video.mkv'), 
        '--delete-track-statistics-tags', 
        '--edit', 'info', 
        '--delete', 'date', 
        '--delete', 'title', 
        '--tags', 'all:', 
        '--set', 'writing-application=', 
        '--set', 'muxing-application='
    ]

    #輸出
    ff = FFmpeg(
        inputs = input_video_file, # pyright: ignore[reportArgumentType]
        outputs = {(finish_dir / 'video.mkv'): ffmpeg_options}, # pyright: ignore[reportArgumentType]
    )
    print()
    ff.run()
    print()
    subprocess.run(meta_clear_options)

    #刪除輸入檔案
    Path.unlink(temp_dir / 'cover.jpg')
    for f in input_video_file.keys():
        f.unlink()

#json處理
def json_process(video_info: dict, finish_dir: Path):
    #變數定義
    output_comment: dict = {} #留言內文
    output_live_chat: dict = {} #聊天室內文

    #獲取發布或上傳日期
    date_input = video_info.get('release_date') or video_info.get('upload_date')
    release_date = date.strptime(date_input, '%Y%m%d').strftime('%Y/%m/%d')  # pyright: ignore[reportArgumentType]

    #影片資訊內文
    output_info: str = (
        '標題:\n'
        f'{video_info['title']}\n'
        '\n'
        '發布日期:\n'
        f'{release_date}\n'
        '\n'
        '影片網址:\n'
        f'{video_info['webpage_url']}\n'
        '\n'
        '說明欄:\n'
        f'{video_info['description']}'
    )
    
    #說明欄處理
    with open((finish_dir / 'info.txt'), 'w') as f:
        f.write(output_info)

    #留言json處理與寫入
    for i, comment in enumerate(video_info['comments']):
        output_comment[f'第{i+1}條留言'] = comment
    with open((finish_dir / f'comment_{date.today().strftime('%Y%m%d')}.json'), 'w') as f:
        json.dump(output_comment, f, indent=4, ensure_ascii=False)

    #聊天室json處理與寫入
    if Path.exists(temp_dir / 'live_chat.json'):
        with open(temp_dir / 'live_chat.json') as f:
            for i, live_chat in enumerate(f):
                output_live_chat[f'第{i+1}條訊息'] = json.loads(live_chat)
        with open((finish_dir / 'live_chat.json'), 'w') as f:
            json.dump(output_live_chat, f, indent=4, ensure_ascii=False)

#par2處理
def par2_process(finish_dir: Path):
    #par2參數設定
    par2_options = [
        'par2', 'c', 
        '-r10', '-b8000', '-n1', 
        (finish_dir / 'check.par2'), 
    ]

    #遞歸檔案清單
    for f in finish_dir.iterdir():
        par2_options += [f]
    
    #較驗檔創建與驗證
    print()
    subprocess.run(par2_options)
    par2_verify = subprocess.run(['par2', 'v', (finish_dir / 'check.par2')], capture_output=True, text=True)
    if 'All files are correct, repair is not required.' not in par2_verify.stdout:
        for f in finish_dir.glob('*.par2'):
            f.unlink()
        print('par2檔案未能成功創建，請嘗試手動創建')

if __name__ == '__main__':
    temp_init()
    try:
        urls = urls_preprocess()
        video_info, finish_dir = download(urls)
        merge(finish_dir)
        json_process(video_info, finish_dir)
        par2_process(finish_dir)
    except KeyboardInterrupt:
        sys.exit('\n')
    finally:
        temp_init()