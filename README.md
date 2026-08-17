# python video backup

python編寫的備份腳本，為封存設計。

整合了`yt-dlp`, `ffmpeg`, `mkvpropedit`, `par2`, `JPEG XL`

可在目錄下創建urls.txt實現多部影片的下載(一部影片一行)

不使用AI編寫(沒錢)

## 依賴項
腳本使用了
- [uv](https://docs.astral.sh/uv)
- [ffmpeg](https://ffmpeg.org)
- [mkvpropedit](https://mkvtoolnix.download)
- [par2](https://github.com/Parchive/par2cmdline/releases)
- [JPEG XL](https://github.com/libjxl/libjxl/releases)

請確定運行前安裝了它，並加入環境目錄

yt-dlp會隨後續`uv sync`安裝

## 使用
```
git clone https://github.com/kumo27/python-video-backup.git
cd python-video-backup
uv sync -U --no-dev
uv run main.py
```

## 待辦事項
- [x] 下載多個連結
- [x] 僅更新留言
- [x] 從播放清單的匯入
- [ ] par2的自動化參數調整
- [x] 支援並行下載
- [x] 留言區markdown處理
- [ ] 聊天室markdown處理，與YT自訂貼圖的下載
- [ ] 增加對 Twitch 的支援
- [ ] 補齊測試
- [ ] 增加錯誤處理 (提交過程中慢慢加)
- [ ] 發現該專案的「你」的想法...

## 注意事項
你現在位於開發分支，請不要將他用於生產環境  
因為開發者英文不好，所以使用中文打註解，錯誤處理之後有空會慢慢加上去，遇到丟問題issue，有空修

<!--
小知識
- 其實倉庫最原始的初始提交在5/28  
  之後提交了約40多個提交後刪庫重建了  
  也就是現在的這倉庫
-->