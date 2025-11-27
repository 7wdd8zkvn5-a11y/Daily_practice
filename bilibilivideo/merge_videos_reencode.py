#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并视频并重新编码（支持精确跳转）
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


def estimate_time(num_files, avg_duration_minutes=10):
    """
    估算重新编码时间
    
    参数:
        num_files: 文件数量
        avg_duration_minutes: 平均每个文件时长（分钟）
    """
    # 重新编码大约是实时播放速度的 0.5-2 倍（取决于硬件）
    # 假设平均 1 倍速度
    total_minutes = num_files * avg_duration_minutes
    
    # 假设编码速度为 1x（实时）
    estimated_minutes = total_minutes
    
    hours = estimated_minutes // 60
    minutes = estimated_minutes % 60
    
    return hours, minutes


def merge_videos_reencode(video_files, output_file='merged_output_seekable.mp4'):
    """
    合并视频并重新编码（支持精确跳转）
    
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
    total_size = 0
    for i, f in enumerate(video_files, 1):
        file_size = f.stat().st_size / (1024 * 1024)  # MB
        total_size += file_size
        print(f"{i:2d}. {f.name} ({file_size:.1f} MB)")
    
    print("-" * 50)
    print(f"总大小: {total_size/1024:.2f} GB")
    
    # 估算时间
    hours, minutes = estimate_time(len(video_files))
    print(f"⏱️  预计需要时间: {hours} 小时 {minutes} 分钟")
    print("    （重新编码需要较长时间，但可以精确跳转）")
    print()
    
    # 创建文件列表
    list_file = 'filelist.txt'
    with open(list_file, 'w', encoding='utf-8') as f:
        for video in video_files:
            abs_path = video.absolute()
            escaped_path = str(abs_path).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    print(f"开始合并并重新编码...")
    print(f"输出文件: {output_file}")
    print()
    print("编码设置:")
    print("  - 视频编码: H.264 (高质量)")
    print("  - 音频编码: AAC")
    print("  - 关键帧间隔: 2秒 (支持精确跳转)")
    print()
    
    start_time = time.time()
    
    # ffmpeg 合并并重新编码命令
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file,
        # 视频编码设置
        '-c:v', 'libx264',           # H.264 编码器
        '-preset', 'medium',          # 编码速度（faster/medium/slow）
        '-crf', '23',                 # 质量（18-28，越小质量越好）
        '-g', '60',                   # 关键帧间隔（每2秒一个，假设30fps）
        '-keyint_min', '60',          # 最小关键帧间隔
        '-sc_threshold', '0',         # 禁用场景切换检测
        # 音频编码设置
        '-c:a', 'aac',                # AAC 音频编码
        '-b:a', '192k',               # 音频比特率
        # 其他设置
        '-movflags', '+faststart',    # 优化网络播放
        '-y',                         # 覆盖输出文件
        output_file
    ]
    
    try:
        # 运行 ffmpeg
        process = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        elapsed_hours = int(elapsed // 3600)
        elapsed_min = int((elapsed % 3600) // 60)
        elapsed_sec = int(elapsed % 60)
        
        print()
        print("=" * 50)
        print(f"✅ 合并完成！")
        print(f"⏱️  实际用时: {elapsed_hours} 小时 {elapsed_min} 分 {elapsed_sec} 秒")
        print(f"📁 输出文件: {output_file}")
        
        # 显示输出文件大小
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file) / (1024 * 1024 * 1024)  # GB
            print(f"📦 文件大小: {output_size:.2f} GB")
        
        print()
        print("✨ 现在可以在视频中任意位置跳转了！")
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
        print("\n❌ 未找到 ffmpeg")
        if os.path.exists(list_file):
            os.remove(list_file)
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
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


def main():
    print("=" * 50)
    print("视频合并工具（重新编码版本）")
    print("=" * 50)
    print()
    
    # 检查 ffmpeg
    if not check_ffmpeg():
        print("❌ 未检测到 ffmpeg")
        print("请先安装: conda install ffmpeg")
        sys.exit(1)
    
    # 获取视频文件
    video_files = get_video_files('downloads')
    
    if not video_files:
        print("❌ downloads 目录下没有找到视频文件")
        sys.exit(1)
    
    # 确认
    print("⚠️  注意：重新编码需要较长时间，但可以解决跳转卡顿问题")
    response = input("是否继续？(y/n): ")
    
    if response.lower() != 'y':
        print("已取消")
        sys.exit(0)
    
    print()
    
    # 合并视频
    output_file = 'merged_video_seekable.mp4'
    success = merge_videos_reencode(video_files, output_file)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
