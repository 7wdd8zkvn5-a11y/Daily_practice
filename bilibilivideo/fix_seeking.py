#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复已合并视频的跳转问题（快速方法）
"""

import os
import subprocess
import sys
import time


def fix_video_seeking(input_file, output_file=None):
    """
    修复视频跳转问题
    
    参数:
        input_file: 输入视频文件
        output_file: 输出文件名（可选）
    """
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        return False
    
    if output_file is None:
        name, ext = os.path.splitext(input_file)
        output_file = f"{name}_fixed{ext}"
    
    file_size = os.path.getsize(input_file) / (1024 * 1024 * 1024)  # GB
    
    print("=" * 50)
    print("修复视频跳转问题")
    print("=" * 50)
    print(f"输入文件: {input_file}")
    print(f"文件大小: {file_size:.2f} GB")
    print(f"输出文件: {output_file}")
    print()
    print("修复方法: 重建关键帧索引")
    print("预计时间: 10-30 分钟（取决于文件大小和硬件）")
    print()
    
    start_time = time.time()
    
    # 使用较快的编码参数
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-c:v', 'libx264',
        '-preset', 'faster',          # 更快的编码速度
        '-crf', '23',
        '-g', '60',                   # 每2秒一个关键帧
        '-keyint_min', '60',
        '-sc_threshold', '0',
        '-c:a', 'copy',               # 音频直接复制，不重新编码
        '-movflags', '+faststart',
        '-y',
        output_file
    ]
    
    try:
        print("开始处理...")
        print()
        
        subprocess.run(cmd, check=True)
        
        end_time = time.time()
        elapsed = end_time - start_time
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        
        print()
        print("=" * 50)
        print(f"✅ 修复完成！")
        print(f"⏱️  用时: {elapsed_min} 分 {elapsed_sec} 秒")
        print(f"📁 输出文件: {output_file}")
        
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file) / (1024 * 1024 * 1024)
            print(f"📦 文件大小: {output_size:.2f} GB")
        
        print()
        print("✨ 现在可以正常跳转了！")
        print("=" * 50)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 处理失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return False


def main():
    # 默认处理 merged_video.mp4
    input_file = 'merged_video.mp4'
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        print()
        print("使用方法:")
        print(f"  python {sys.argv[0]} [视频文件]")
        print()
        print("示例:")
        print(f"  python {sys.argv[0]} merged_video.mp4")
        sys.exit(1)
    
    success = fix_video_seeking(input_file)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
