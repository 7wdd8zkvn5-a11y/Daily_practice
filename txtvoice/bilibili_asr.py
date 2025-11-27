#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili 视频离线语音识别工具 - 增强版
功能：下载B站视频 → 提取音频 → 分段处理 → ASR识别 → 输出字幕/文本
作者：AI助手
版本：2.0
"""

import os
import sys
import subprocess
import re
import shutil
import time
import logging
import argparse
import json
from contextlib import contextmanager
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import timedelta

# 第三方库导入
try:
    from modelscope.hub.snapshot_download import snapshot_download
    from funasr import AutoModel
    import torch
    from tqdm import tqdm
except ImportError as e:
    print(f"❌ 缺少必要依赖: {e}")
    print("请运行: pip install modelscope funasr torch tqdm moviepy")
    sys.exit(1)

# ==================== 日志配置 ====================
def setup_logging(log_file: Path) -> logging.Logger:
    """配置日志系统（同时输出到控制台和文件）"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# ==================== 核心配置 ====================
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "VIDEO_URL": "https://www.bilibili.com/video/BV1gsU5BVEcK",
    "MODEL_ID": "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    "MODEL_REVISION": "v2.0.4",
    "HOTWORDS_STR": "罗永浩,锤子科技,Smartisan,工匠精神,创新型企业,用户体验,产品经理,何同学,5G,AI",
    "CHUNK_DURATION": 300,
    "OUTPUT_DIR": "outputs",
    "AUDIO_TEMP_DIR": "temp/audio",
    "VIDEO_DOWNLOAD_DIR": "downloads",
    "LOCAL_MODEL_DIR": "funasr_model",
    "TRANSLATE": False,
    "KEEP_TEMP": False
}

# 加载或创建配置文件
def load_config() -> Dict[str, Any]:
    """加载配置文件或使用默认值"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 合并缺失的配置项
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}, 使用默认配置")
    
    # 创建默认配置文件
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
    
    return DEFAULT_CONFIG.copy()

# 初始化配置
CONFIG = load_config()
logger = setup_logging(BASE_DIR / "processing.log")

# 从配置中读取参数
VIDEO_URL = CONFIG["VIDEO_URL"]
MODEL_ID = CONFIG["MODEL_ID"]
MODEL_REVISION = CONFIG["MODEL_REVISION"]
HOTWORDS_STR = CONFIG["HOTWORDS_STR"]
CHUNK_DURATION = CONFIG["CHUNK_DURATION"]
OUTPUT_DIR = BASE_DIR / CONFIG["OUTPUT_DIR"]
AUDIO_TEMP_DIR = BASE_DIR / CONFIG["AUDIO_TEMP_DIR"]
VIDEO_DOWNLOAD_DIR = BASE_DIR / CONFIG["VIDEO_DOWNLOAD_DIR"]
LOCAL_MODEL_DIR = BASE_DIR / CONFIG["LOCAL_MODEL_DIR"]
TRANSLATE = CONFIG["TRANSLATE"]
KEEP_TEMP = CONFIG["KEEP_TEMP"]

# ==================== 工具函数 ====================
@contextmanager
def timer(label: str):
    """计时上下文管理器"""
    start = time.time()
    yield
    elapsed = time.time() - start
    logger.info(f"⏱️ {label} 耗时: {elapsed:.2f}秒")

def safe_remove(path: Path):
    """安全删除文件或目录"""
    try:
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            logger.debug(f"已删除: {path}")
    except Exception as e:
        logger.warning(f"无法删除 {path}: {str(e)}")

def is_cuda_available() -> bool:
    """检查CUDA是否可用"""
    try:
        return torch.cuda.is_available()
    except:
        return False

# ==================== 依赖检查 ====================
def check_dependencies():
    """检查必要的外部工具"""
    deps = {
        "you-get": "you-get --version",
        "ffmpeg": "ffmpeg -version",
        "ffprobe": "ffprobe -version"
    }
    
    missing = []
    for name, cmd in deps.items():
        try:
            subprocess.run(cmd, shell=True, check=True, 
                         capture_output=True, timeout=5)
        except:
            missing.append(name)
    
    if missing:
        logger.error(f"❌ 缺少依赖工具: {', '.join(missing)}")
        logger.info("请安装: ")
        logger.info("  you-get: pip install you-get")
        logger.info("  ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)

# ==================== 模型管理 ====================
def download_model_if_needed(model_id: str, local_path: Path, revision: str = None) -> str:
    """自动下载模型（增强版）"""
    # 检查模型完整性
    required_files = ["configuration.json", "model.pb", "vocab.txt"]
    
    if local_path.exists():
        files_exist = all((local_path / f).exists() for f in required_files)
        if files_exist:
            logger.info(f"✅ 本地模型完整: {local_path}")
            return str(local_path)
        else:
            logger.warning("⚠️ 本地模型不完整，重新下载...")
            safe_remove(local_path)
    
    logger.info(f"📦 正在下载模型: {model_id}")
    try:
        # 修改调用方式，适配 modelscope 1.4.0 API
        downloaded_path = snapshot_download(
            model_id,
            revision=revision,
            cache_dir=str(local_path)  # 改为 cache_dir 参数
        )
        logger.info(f"✅ 模型下载完成: {downloaded_path}")
        return downloaded_path
    except Exception as e:
        logger.error(f"❌ 模型下载失败: {e}")
        logger.info("💡 尝试: pip install -U modelscope")
        sys.exit(1)

# ==================== 文件处理 ====================
def ensure_dirs():
    """确保目录存在"""
    for dir_path in [OUTPUT_DIR, AUDIO_TEMP_DIR, VIDEO_DOWNLOAD_DIR, LOCAL_MODEL_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def download_bilibili_video(url: str) -> Path:
    """下载B站视频（增强错误处理）"""
    logger.info(f"📥 正在下载视频: {url.strip()}")
    
    # 清空下载目录
    for f in VIDEO_DOWNLOAD_DIR.glob("*"):
        if f.is_file():
            safe_remove(f)
    
    cmd = f'you-get -o "{VIDEO_DOWNLOAD_DIR}" "{url.strip()}"'
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, 
            encoding='utf-8', timeout=600
        )
        
        if result.returncode != 0:
            logger.error(f"下载失败: {result.stderr}")
            raise RuntimeError(f"视频下载失败: {result.stderr}")
        
        # 查找下载的视频文件
        video_files = list(VIDEO_DOWNLOAD_DIR.glob("*.mp4")) + \
                      list(VIDEO_DOWNLOAD_DIR.glob("*.flv")) + \
                      list(VIDEO_DOWNLOAD_DIR.glob("*.mkv")) + \
                      list(VIDEO_DOWNLOAD_DIR.glob("*.webm"))
        
        if not video_files:
            raise FileNotFoundError("未找到下载的视频文件")
        
        logger.info(f"✅ 视频下载完成: {video_files[0]}")
        return video_files[0]
    
    except subprocess.TimeoutExpired:
        logger.error("❌ 视频下载超时")
        raise
    except Exception as e:
        logger.exception(f"下载过程中发生意外错误: {str(e)}")
        raise

def extract_audio(video_path: Path) -> Path:
    """提取音频（增强错误处理）"""
    logger.info("🎵 正在提取音频...")
    
    # 清空音频临时目录
    for f in AUDIO_TEMP_DIR.glob("*.wav"):
        safe_remove(f)
    
    final_wav = AUDIO_TEMP_DIR / f"{video_path.stem}_16k.wav"
    
    try:
        subprocess.run([
            "ffmpeg", "-i", str(video_path), "-ac", "1", "-ar", "16000", "-y",
            "-acodec", "pcm_s16le", str(final_wav)
        ], check=True, capture_output=True, timeout=600)
        
        logger.info(f"✅ 音频提取完成: {final_wav}")
        return final_wav
    
    except subprocess.CalledProcessError as e:
        logger.error(f"音频提取失败: {e.stderr.decode('utf-8')}")
        raise
    except Exception as e:
        logger.exception(f"音频提取过程中发生意外错误: {str(e)}")
        raise

def get_audio_duration(audio_path: Path) -> float:
    """获取音频时长（增强错误处理）"""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
        ], capture_output=True, text=True, check=True, encoding='utf-8', timeout=30)
        
        return float(result.stdout.strip())
    
    except subprocess.CalledProcessError as e:
        logger.error(f"获取音频时长失败: {e.stderr}")
        raise
    except Exception as e:
        logger.exception(f"获取音频时长时发生意外错误: {str(e)}")
        raise

def split_audio_into_chunks(audio_path: Path, chunk_duration: int) -> List[Tuple[Path, float]]:
    """分段音频（增强错误处理）"""
    total_duration = get_audio_duration(audio_path)
    chunks = []
    start = 0.0
    idx = 0
    
    logger.info(f"🔪 正在分段音频（每段 {chunk_duration} 秒，共 {total_duration/60:.1f} 分钟）...")
    
    with tqdm(total=int(total_duration), desc="分段进度", unit="秒") as pbar:
        while start < total_duration:
            current_dur = min(chunk_duration, total_duration - start)
            chunk_path = AUDIO_TEMP_DIR / f"chunk_{idx:04d}.wav"
            
            try:
                subprocess.run([
                    "ffmpeg", "-ss", str(start), "-t", str(current_dur),
                    "-i", str(audio_path), "-ac", "1", "-ar", "16000",
                    "-acodec", "pcm_s16le", "-y", str(chunk_path)
                ], check=True, capture_output=True, timeout=600)
                
                chunks.append((chunk_path, start))
                
            except subprocess.CalledProcessError as e:
                logger.error(f"分段 {idx} 失败: {e.stderr.decode('utf-8')}")
                # 创建空文件占位
                chunk_path.touch()
                chunks.append((chunk_path, start))
            
            except Exception as e:
                logger.exception(f"分段 {idx} 发生意外错误: {str(e)}")
                chunks.append((chunk_path, start))
            
            start += chunk_duration
            idx += 1
            pbar.update(int(current_dur))
    
    logger.info(f"✅ 分段完成：共 {len(chunks)} 段")
    return chunks

# ==================== ASR 识别 ====================
def transcribe_with_funasr(chunks: List[Tuple[Path, float]], hotwords: str) -> List[Tuple[float, str]]:
    """使用 FunASR 进行语音识别（增强版）"""
    logger.info("🎙️ 正在加载 FunASR 模型...")
    
    # 确保模型已下载
    model_path = download_model_if_needed(MODEL_ID, LOCAL_MODEL_DIR, MODEL_REVISION)
    
    try:
        # 自动选择设备
        device = "cuda:0" if is_cuda_available() else "cpu"
        logger.info(f"💻 使用设备: {device.upper()}")
        
        model = AutoModel(
            model=model_path,
            hotword=hotwords,
            disable_update=True,
            device=device
        )
    except Exception as e:
        logger.error(f"❌ 模型加载失败: {e}")
        raise
    
    results = []
    with tqdm(total=len(chunks), desc="识别进度", unit="段") as pbar:
        for chunk_path, offset in chunks:
            try:
                res = model.generate(input=str(chunk_path))
                text = res[0]["text"] if res and len(res) > 0 else ""
                results.append((offset, text))
            except Exception as e:
                logger.warning(f"分段 {chunk_path.name} 识别失败: {e}")
                results.append((offset, ""))
            finally:
                pbar.update(1)
    
    # 释放显存
    try:
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except:
        pass
    
    return results

# ==================== 后处理 ====================
def apply_smart_corrections(text: str) -> str:
    """智能热词修正（增强版）"""
    corrections = {
        # 可以在这里添加特定的纠错规则
        " ": "",  # 示例：移除多余的空格
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    return text.strip()

def format_timestamp(seconds: float) -> str:
    """格式化时间戳为 SRT 格式"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def save_results(results: List[Tuple[float, str]], output_path: Path):
    """保存识别结果为SRT和TXT格式"""
    # 保存为TXT格式
    txt_path = output_path.with_suffix('.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for _, text in results:
            if text.strip():
                f.write(f"{text}\n")
    
    logger.info(f"📄 文本结果已保存: {txt_path}")
    
    # 保存为SRT格式（字幕文件）
    srt_path = output_path.with_suffix('.srt')
    with open(srt_path, 'w', encoding='utf-8') as f:
        idx = 1
        for offset, text in results:
            if text.strip():
                start_time = format_timestamp(offset)
                end_time = format_timestamp(offset + 5)  # 假设每段5秒
                
                f.write(f"{idx}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
                idx += 1
    
    logger.info(f"🎬 字幕文件已保存: {srt_path}")

def cleanup_temp_files():
    """清理临时文件"""
    if not KEEP_TEMP:
        logger.info("🧹 正在清理临时文件...")
        safe_remove(AUDIO_TEMP_DIR)
        safe_remove(VIDEO_DOWNLOAD_DIR)
        # 保留模型文件以便下次使用
        logger.info("✅ 临时文件清理完成")

# ==================== 主程序 ====================
def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="Bilibili 视频离线语音识别工具")
    parser.add_argument("--url", help="B站视频URL", default=VIDEO_URL)
    parser.add_argument("--output", help="输出文件名（不含扩展名）", default="transcription")
    args = parser.parse_args()
    
    try:
        # 检查依赖
        check_dependencies()
        
        # 确保目录存在
        ensure_dirs()
        
        # 下载视频
        with timer("视频下载"):
            video_path = download_bilibili_video(args.url)
        
        # 提取音频
        with timer("音频提取"):
            audio_path = extract_audio(video_path)
        
        # 分段音频
        with timer("音频分段"):
            chunks = split_audio_into_chunks(audio_path, CHUNK_DURATION)
        
        # ASR识别
        with timer("语音识别"):
            results = transcribe_with_funasr(chunks, HOTWORDS_STR)
        
        # 保存结果
        output_path = OUTPUT_DIR / args.output
        save_results(results, output_path)
        
        # 清理临时文件
        cleanup_temp_files()
        
        logger.info("🎉 所有处理完成！")
        
    except KeyboardInterrupt:
        logger.info("⏹️ 用户中断程序")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ 程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()