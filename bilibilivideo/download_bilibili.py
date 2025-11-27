#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载工具
支持单个视频和多P视频下载
"""

import subprocess
import sys
import os


def check_yt_dlp():
    """检查 yt-dlp 是否已安装"""
    try:
        subprocess.run(['yt-dlp', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_yt_dlp():
    """安装 yt-dlp"""
    print("正在安装 yt-dlp...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'],
                      check=True)
        print("yt-dlp 安装成功！")
        return True
    except subprocess.CalledProcessError:
        print("安装失败，请手动运行: pip install yt-dlp")
        return False


def download_bilibili_video(bv_id, output_dir='downloads', cookie_file=None):
    """
    下载B站视频（支持多P）
    
    参数:
        bv_id: B站视频的BV号，例如 'BV1T2k6BaEeC'
        output_dir: 下载保存目录
        cookie_file: cookie文件路径（可选，用于下载高清或会员视频）
    """
    # 创建下载目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 构建完整URL
    url = f'https://www.bilibili.com/video/{bv_id}'
    
    print(f"开始下载: {url}")
    print(f"保存位置: {output_dir}")
    
    # 检查cookie文件
    if cookie_file and os.path.exists(cookie_file):
        print(f"使用 Cookie: {cookie_file}")
        print("提示: 使用 Cookie 可以下载更高画质")
    else:
        print("提示: 未使用 Cookie，可能只能下载普通画质")
        print("      如需高清画质，请参考 README.md 配置 Cookie")
    
    print("-" * 50)
    
    # yt-dlp 下载命令
    cmd = [
        'yt-dlp',
        '--yes-playlist',  # 下载播放列表（多P视频）
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # 最佳画质
        '-o', f'{output_dir}/%(title)s-P%(playlist_index)s.%(ext)s',  # 输出格式
        '--merge-output-format', 'mp4',  # 合并为mp4格式
    ]
    
    # 如果提供了cookie文件，添加到命令中
    if cookie_file and os.path.exists(cookie_file):
        cmd.extend(['--cookies', cookie_file])
    
    cmd.append(url)
    
    try:
        subprocess.run(cmd, check=True)
        print("\n下载完成！")
    except subprocess.CalledProcessError as e:
        print(f"\n下载失败: {e}")
        sys.exit(1)


def main():
    # 检查并安装 yt-dlp
    if not check_yt_dlp():
        print("未检测到 yt-dlp")
        if not install_yt_dlp():
            sys.exit(1)
    
    # 下载视频
    bv_id = 'BV1T2k6BaEeC'
    
    # Cookie 文件路径（如果存在）
    cookie_file = 'bilibili_cookies.txt'
    
    # 如果没有 cookie 文件，设置为 None
    if not os.path.exists(cookie_file):
        cookie_file = None
    
    download_bilibili_video(bv_id, cookie_file=cookie_file)


if __name__ == '__main__':
    main()
