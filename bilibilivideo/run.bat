@echo off
REM 快速运行脚本

echo 激活 Conda 环境...
call conda activate bilibili_dl

echo 开始下载视频...
python download_bilibili.py

pause
