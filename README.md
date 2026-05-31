# python video backup

python編寫的，個人用的網路備份腳本，為封存網路影片設計。

整合了`yt-dlp`, `ffmpeg`, `mkvpropedit`, `par2`

不使用AI編寫(沒錢)

## 依賴項
腳本使用了
- [uv](https://docs.astral.sh/uv)
- [ffmpeg](https://ffmpeg.org)
- [mkvpropedit](https://mkvtoolnix.download)
- [par2](https://github.com/Parchive/par2cmdline/releases)

請確定運行前安裝了它，並加入環境目錄

yt-dlp會隨後續`uv sync`安裝

## 使用
```
git clone https://github.com/kumo27/python-video-backup.git
cd python-video-backup
uv sync
uv run main.py
```

## 待辦事項
- [ ] 增加錯誤處理
- [ ] 支援多連結下載
- [ ] 增加對 Twitch 的支援

## 注意事項
因為主要為個人使用，所以沒寫什麼錯誤處理，之後有空會慢慢加上去，遇到丟問題issue，有空修