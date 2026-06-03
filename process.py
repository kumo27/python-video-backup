import json
import subprocess
from ffmpy import FFmpeg
from pathlib import Path
from config import temp_dir
from datetime import date

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