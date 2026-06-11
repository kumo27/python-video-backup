import json
import time
import logging
import subprocess
from ffmpy import FFmpeg
from pathlib import Path
from datetime import date
from config import log_root
from contextlib import chdir

logger = logging.getLogger(f'{log_root}.{__name__}')

class PostProcess:
    '''後處理模塊'''
    def __init__(self, temp_dir: Path, finish_dir: Path) -> None:
        self.temp_dir = temp_dir
        self.finish_dir = finish_dir

    def merge(self):
        '''影片、音訊與字幕合併，並包含元數據清理'''
        #變數定義
        input_video_file: dict[Path, None] = {} #輸入ffmpeg的檔案
        ffmpeg_opts: list = [] #ffmpeg的輸出參數
        sub_lang: list = [] #後續的語言標籤
        
        #合併影片與字幕
        for file_path in self.temp_dir.iterdir():
            if file_path.suffix in ['.mp4', '.webm']:
                logger.debug(f'影片或音訊檔: {file_path.name}')
                input_video_file[file_path] = None
            elif file_path.suffix in ['.vtt', '.srt']:
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
            '-attach', (self.temp_dir / 'cover.jpg'), '-metadata:s:t', 'mimetype=image/jpeg', 
            '-c', 'copy', 
            '-loglevel', 'warning', '-hide_banner', '-stats'
        ]

        #影片元數據清理參數
        meta_clear_opts = [
            'mkvpropedit', (self.finish_dir / 'video.mkv'), 
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
            outputs = {(self.finish_dir / 'video.mkv'): ffmpeg_opts}, # pyright: ignore[reportArgumentType]
        )
        print()
        logger.debug(ff.cmd)
        ff.run()
        print()
        subprocess.run(meta_clear_opts)

        #刪除輸入檔案
        Path.unlink(self.temp_dir / 'cover.jpg')
        for f in input_video_file.keys():
            f.unlink()

    def json_process(self, video_info: dict):
        '''元數據json的處理模塊'''
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
        with open((self.finish_dir / 'info.txt'), 'w') as f:
            f.write(output_info)

        #留言json處理與寫入
        for i, comment in enumerate(video_info['comments']):
            output_comment[f'第{i+1}條留言'] = comment
        with open((self.finish_dir / f'comment_{date.today().strftime('%Y%m%d')}.json'), 'w') as f:
            json.dump(output_comment, f, indent=4, ensure_ascii=False)

        #聊天室json處理與寫入
        if Path.exists(self.temp_dir / 'live_chat.json'):
            with open(self.temp_dir / 'live_chat.json') as f:
                for i, live_chat in enumerate(f):
                    output_live_chat[f'第{i+1}條訊息'] = json.loads(live_chat)
            with open((self.finish_dir / 'live_chat.json'), 'w') as f:
                json.dump(output_live_chat, f, indent=4, ensure_ascii=False)

    def par2_process(self):
        '''par2檔案處理模塊'''
        #切換工作路徑
        with chdir(self.finish_dir):
            logger.debug(f'切換工作目錄: {self.finish_dir}')
            #par2參數設定
            par2_opts = [
                'par2', 'c', 
                '-r30', '-b10000', '-n1', 
                'check.par2', 
            ]

            #遞歸檔案清單
            for f in self.finish_dir.iterdir():
                f = f.relative_to(Path.cwd())
                par2_opts += [f]
            
            #校驗檔創建與驗證
            print()
            logger.debug(par2_opts)
            subprocess.run(par2_opts)
            par2_verify = subprocess.run(['par2', 'v', 'check.par2'], capture_output=True, text=True)
            if par2_verify.returncode != 0:
                for f in self.finish_dir.glob('*.par2'):
                    f.unlink()
                print()
                logger.error('par2檔案未能成功創建，請嘗試手動創建')
                time.sleep(2)
