import json
import requests
import subprocess
from ffmpy import FFmpeg
from pathlib import Path
from datetime import date
from yt_dlp import YoutubeDL

#全域變數
temp_dir: Path = Path.cwd() / 'temp' #緩存目錄

#初始化
def temp_init():
    if temp_dir.exists() == True:
        for f in temp_dir.iterdir():
            f.unlink()
    temp_dir.mkdir(exist_ok=True)

#下載
def download(urls: str) -> tuple[dict, Path]:
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
        'cookiesfrombrowser': ('brave', ), 
    }

    #下載
    with YoutubeDL(ydl_opts) as ydl: # pyright: ignore[reportArgumentType]
        ydl.download(urls)

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
        if not file_path.suffix in ['.json', '.jpg', '.txt']:
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
    output_comment: dict = {}
    output_live_chat: dict = {}
    output_description: str = (
        '標題:\n'
        f'{video_info['title']}\n'
        '\n'
        '發布日期:\n'
        f'{date.strptime(video_info['release_date'], '%Y%m%d').strftime('%Y/%m/%d')}\n'
        '\n'
        '影片網址:\n'
        f'{video_info['webpage_url']}\n'
        '\n'
        '說明欄:\n'
        f'{video_info['description']}'
    )
    
    #說明欄處理
    with open((finish_dir / 'info.txt'), 'w') as f:
        f.write(output_description)

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

def par2_treatment(finish_dir: Path):
    par2_options = [
        'par2', 'c', 
        '-r10', '-b8000', '-n1', 
        (finish_dir / 'check.par2'), 
    ]
    for f in finish_dir.iterdir():
        par2_options += [f]
    
    print()
    subprocess.run(par2_options)
    par2_verify = subprocess.run(['par2', 'v', (finish_dir / 'check.par2')], capture_output=True, text=True)
    
    if 'All files are correct, repair is not required.' not in par2_verify.stdout:
        for f in finish_dir.glob('*.par2'):
            f.unlink()
        print('par2檔案未能成功創建，請嘗試手動創建')


if __name__ == '__main__':
    temp_init()
    video_info, finish_dir = download(input('請輸入影片網址: '))
    merge(finish_dir)
    json_process(video_info, finish_dir)
    par2_treatment(finish_dir)