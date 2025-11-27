#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并多个视频文件为一个 MP4
"""

import os
import subprocess
import sys
from pathlib import Path
import time


def get_video_files(directory='downloads'):
    """获取目录下所有视频文件并排序"""
    video_extensions = ['.mp4', '.flv', '.mkv', '.avi']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(Path(directory).glob(f'*{ext}'))
    
    # 按文件名排序
    video_files.sort(key=lambda x: x.name)
    
    return video_files


def estimate_time(num_files, avg_file_size_mb=100):
    """
    估算合并时间
    
    参数:
        num_files: 文件数量
        avg_file_size_mb: 平均文件大小（MB）
    """
    # 粗略估算：每个文件约需要 2-5 秒处理时间（取决于电脑性能）
    # 使用 concat 方法（无需重新编码）会很快
    estimated_seconds = num_files * 3  # 平均每个文件 3 秒
    
    minutes = estimated_seconds // 60
    seconds = estimated_seconds % 60
    
    return minutes, seconds


def merge_videos_concat(video_files, output_file='merged_output.mkv'):
    """
    使用 ffmpeg concat 方法合并视频（最快，无需重新编码）
    
    参数:
        video_files: 视频文件列表
        output_file: 输出文件名
    """
    if not video_files:
        print("❌ 未找到视频文件")
        return False
    
    print(f"找到 {len(video_files)} 个视频文件")
    print("-" * 50)
    
    # 显示文件列表
    for i, f in enumerate(video_files, 1):
        file_size = f.stat().st_size / (1024 * 1024)  # MB
        print(f"{i:2d}. {f.name} ({file_size:.1f} MB)")
    
    print("-" * 50)
    
    # 估算时间
    minutes, seconds = estimate_time(len(video_files))
    print(f"⏱️  预计需要时间: {minutes} 分 {seconds} 秒")
    print()
    
    # 创建文件列表
    list_file = 'filelist.txt'
    with open(list_file, 'w', encoding='utf-8') as f:
        for video in video_files:
            # 使用绝对路径，避免路径问题
            abs_path = video.absolute()
            # 转义单引号
            escaped_path = str(abs_path).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    print(f"开始合并视频...")
    print(f"输出文件: {output_file}")
    print()
    
    start_time = time.time()
    
    # 修改ffmpeg命令
    cmd = [
        'ffmpeg',
        '-hide_banner',  # 隐藏版本信息
        '-fflags', '+genpts+igndts',  # 生成PTS，忽略DTS
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file,
        '-c', 'copy',
        '-max_interleave_delta', '0',
        '-video_track_timescale', '60000',  # 统一时间基准
        '-y',
        output_file
    ]
    
    try:
        # 显示进度
        process = subprocess.run(
            cmd,
            check=True,
            capture_output=False,  # 显示 ffmpeg 输出
            text=True
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        
        print()
        print("=" * 50)
        print(f"✅ 合并完成！")
        print(f"⏱️  实际用时: {elapsed_min} 分 {elapsed_sec} 秒")
        print(f"📁 输出文件: {output_file}")
        
        # 显示输出文件大小
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file) / (1024 * 1024 * 1024)  # GB
            print(f"📦 文件大小: {output_size:.2f} GB")
        
        print("=" * 50)
        
        # 清理临时文件
        os.remove(list_file)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 合并失败: {e}")
        if os.path.exists(list_file):
            os.remove(list_file)
        return False
    except FileNotFoundError:
        print("\n❌ 未找到 ffmpeg，请先安装 ffmpeg")
        print("安装方法:")
        print("  Windows: 下载 https://ffmpeg.org/download.html")
        print("  或使用: conda install ffmpeg")
        if os.path.exists(list_file):
            os.remove(list_file)
        return False


def check_ffmpeg():
    """检查 ffmpeg 是否已安装"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_ffmpeg():
    """尝试安装 ffmpeg"""
    print("正在安装 ffmpeg...")
    try:
        # 尝试使用 conda 安装
        subprocess.run(['conda', 'install', '-n', 'bilibili_dl', 'ffmpeg', '-y'],
                      check=True)
        print("✅ ffmpeg 安装成功！")
        return True
    except:
        print("❌ 自动安装失败")
        print("请手动安装 ffmpeg:")
        print("  方法1: conda install ffmpeg")
        print("  方法2: 从 https://ffmpeg.org/download.html 下载")
        return False


def main():
    print("=" * 50)
    print("视频合并工具")
    print("=" * 50)
    print()
    
    # 检查 ffmpeg
    if not check_ffmpeg():
        print("⚠️  未检测到 ffmpeg")
        if not install_ffmpeg():
            sys.exit(1)
    
    # 获取视频文件
    video_files = get_video_files('downloads')
    
    if not video_files:
        print("❌ downloads 目录下没有找到视频文件")
        sys.exit(1)
    
    # 合并视频
    output_file = 'merged_video.mp4'
    success = merge_videos_concat(video_files, output_file)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
