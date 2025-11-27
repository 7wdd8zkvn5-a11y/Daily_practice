@echo off
REM 快速合并视频

echo 激活 Conda 环境...
call conda activate bilibili_dl

echo 开始合并视频...
python merge_videos.py

pause
