#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载最高画质的 B站视频
"""

import subprocess
import sys
import os


def download_best_quality(bv_id, output_dir='downloads'):
    """下载最高画质视频"""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    url = f'https://www.bilibili.com/video/{bv_id}'
    cookie_file = 'bilibili_cookies.txt'
    
    print(f"下载视频: {url}")
    print(f"画质: 最高可用画质 (1080P)")
    print(f"保存位置: {output_dir}")
    print("-" * 50)
    
    # 下载命令 - 明确指定最高画质
    cmd = [
        'yt-dlp',
        '--cookies', cookie_file,
        '--yes-playlist',  # 下载所有分P
        '-f', 'bestvideo[height<=1080]+bestaudio/best',  # 最高1080P视频+最佳音频
        '-o', f'{output_dir}/%(title)s-P%(playlist_index)s.%(ext)s',
        '--merge-output-format', 'mp4',
        url
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ 下载完成！")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 下载失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # 修改这里的 BV 号
    bv_id = 'BV1T2k6BaEeC'
    download_best_quality(bv_id)
