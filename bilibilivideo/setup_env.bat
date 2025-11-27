@echo off
REM B站视频下载工具 - Conda环境设置脚本

echo ====================================
echo 创建 Conda 虚拟环境
echo ====================================

REM 创建名为 bilibili_dl 的虚拟环境，使用 Python 3.10
call conda create -n bilibili_dl python=3.10 -y

echo.
echo ====================================
echo 激活虚拟环境
echo ====================================

call conda activate bilibili_dl

echo.
echo ====================================
echo 安装依赖库
echo ====================================

REM 安装 yt-dlp
call pip install yt-dlp

echo.
echo ====================================
echo 安装完成！
echo ====================================
echo.
echo 使用方法:
echo 1. 激活环境: conda activate bilibili_dl
echo 2. 运行脚本: python download_bilibili.py
echo.
echo 退出环境: conda deactivate
echo.

pause
