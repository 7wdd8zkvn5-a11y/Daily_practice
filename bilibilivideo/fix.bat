@echo off
REM 修复视频跳转问题

echo 激活 Conda 环境...
call conda activate bilibili_dl

echo 修复视频跳转问题...
python fix_seeking.py merged_video.mp4

pause
