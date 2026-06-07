import json
import logging
import subprocess
from ffmpy import FFmpeg
from pathlib import Path
from datetime import date
from config import log_root
from config import temp_dir
from contextlib import chdir

logger = logging.getLogger(f'{log_root}.{__name__}')

#合併
def merge(finish_dir: Path):
    #變數定義
    input_video_file: dict[Path, None] = {} #輸入ffmpeg的檔案
    ffmpeg_opts: list = [] #ffmpeg的輸出參數
    sub_lang: list = [] #後續的語言標籤
    
    #合併影片與字幕
    for file_path in temp_dir.iterdir():
        logger.debug(f'temp資料夾檔案: {file_path.name}')
        if file_path.suffix in ['.mp4', '.webm']:
            logger.debug(f'影片或音訊檔: {file_path.name}')
            input_video_file[file_path] = None
        elif file_path.suffix in ['.vtt', '.str']:
            logger.debug(f'字幕檔: {file_path.name}')
            sub_lang += [file_path.stem]
            input_video_file[file_path] = None
        else:
            logger.debug(f'其他: {file_path.name}')
            continue

    #處理ffmpeg map
    for i in range(0, len(input_video_file)):
        ffmpeg_opts += ['-map', str(i)]

    for i, lang in enumerate(sub_lang):
        ffmpeg_opts += [f'-metadata:s:s:{i}', f'language={lang}']

    #ffmpeg輸出參數合併
    ffmpeg_opts += [
        '-attach', (temp_dir / 'cover.jpg'), '-metadata:s:t', 'mimetype=image/jpeg', 
        '-c', 'copy', 
        '-loglevel', 'warning', '-hide_banner', '-stats'
    ]

    #影片元數據清理參數
    meta_clear_opts = [
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
        outputs = {(finish_dir / 'video.mkv'): ffmpeg_opts}, # pyright: ignore[reportArgumentType]
    )
    print()
    logger.debug(ff.cmd)
    ff.run()
    print()
    subprocess.run(meta_clear_opts)

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
    #切換工作路徑
    with chdir(finish_dir):
        logger.debug(f'切換工作目錄: {finish_dir}')
        #par2參數設定
        par2_opts = [
            'par2', 'c', 
            '-r10', '-b8000', '-n1', 
            'check.par2', 
        ]

        #遞歸檔案清單
        for f in finish_dir.iterdir():
            f = f.relative_to(Path.cwd())
            par2_opts += [f]
        
        #校驗檔創建與驗證
        print()
        logger.debug(par2_opts)
        subprocess.run(par2_opts)
        par2_verify = subprocess.run(['par2', 'v', 'check.par2'], capture_output=True, text=True)
        if 'All files are correct, repair is not required.' not in par2_verify.stdout:
            for f in finish_dir.glob('*.par2'):
                f.unlink()
            print()
            logger.error('par2檔案未能成功創建，請嘗試手動創建')