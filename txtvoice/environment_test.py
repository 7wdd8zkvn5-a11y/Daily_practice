#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境测试脚本
用于验证Bilibili视频语音识别工具的所有依赖是否正确安装
"""

import sys
import subprocess
import importlib

def test_python_version():
    """测试Python版本"""
    version = sys.version_info
    print(f"🐍 Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python版本满足要求 (>= 3.8)")
        return True
    else:
        print("❌ Python版本不满足要求 (< 3.8)")
        return False

def test_python_package(package_name, display_name=None):
    """测试单个Python包导入"""
    if display_name is None:
        display_name = package_name
    
    try:
        importlib.import_module(package_name)
        print(f"✅ {display_name} ({package_name}) 导入成功")
        return True
    except ImportError as e:
        print(f"❌ {display_name} ({package_name}) 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ {display_name} ({package_name}) 导入异常: {e}")
        return False

def test_python_packages():
    """测试所有必需的Python库"""
    print("\n🔍 测试Python库导入...")
    
    required_packages = [
        ('torch', 'PyTorch'),
        ('torchaudio', 'Torchaudio'),
        ('funasr', 'FunASR'),
        ('modelscope', 'ModelScope'),
        ('tqdm', 'tqdm'),
        ('moviepy', 'MoviePy')
    ]
    
    results = []
    for package, display_name in required_packages:
        result = test_python_package(package, display_name)
        results.append(result)
    
    return all(results)

def test_external_tool(tool_name, version_command):
    """测试外部工具"""
    try:
        result = subprocess.run(
            version_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {tool_name} 可用")
            return True
        else:
            print(f"❌ {tool_name} 不可用: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {tool_name} 测试超时")
        return False
    except Exception as e:
        print(f"❌ {tool_name} 不可用: {e}")
        return False

def test_external_tools():
    """测试外部工具"""
    print("\n🔧 测试外部工具...")
    
    tools = [
        ('you-get', 'you-get --version'),
        ('ffmpeg', 'ffmpeg -version'),
        ('ffprobe', 'ffprobe -version')
    ]
    
    results = []
    for tool_name, command in tools:
        result = test_external_tool(tool_name, command)
        results.append(result)
    
    return all(results)

def test_torch_details():
    """测试PyTorch详细信息"""
    try:
        import torch
        print(f"\n🖥️ PyTorch版本: {torch.__version__}")
        print(f"🎮 CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"🧮 CUDA设备数量: {torch.cuda.device_count()}")
            if torch.cuda.device_count() > 0:
                print(f"💻 当前CUDA设备: {torch.cuda.get_device_name(0)}")
    except Exception as e:
        print(f"❌ PyTorch详细信息测试失败: {e}")

def test_funasr_details():
    """测试FunASR详细信息"""
    try:
        import funasr
        version = getattr(funasr, '__version__', '未知')
        print(f"\n🤖 FunASR版本: {version}")
        print("📝 FunASR库基础功能正常")
    except Exception as e:
        print(f"❌ FunASR详细信息测试失败: {e}")

def test_modelscope_compatibility():
    """测试ModelScope兼容性"""
    try:
        # 测试基本导入
        import modelscope
        version = getattr(modelscope, '__version__', '未知')
        print(f"\n📦 ModelScope版本: {version}")
        
        # 测试关键组件导入
        from modelscope.pipelines import pipeline
        print("✅ ModelScope核心组件导入成功")
        return True
    except TypeError as e:
        if "'type' object is not subscriptable" in str(e):
            print("\n❌ ModelScope兼容性问题:")
            print("   检测到Python版本过低导致的类型注解错误")
            print("   建议升级到Python 3.9或更高版本")
            return False
        else:
            print(f"❌ ModelScope导入失败: {e}")
            return False
    except Exception as e:
        print(f"❌ ModelScope测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试Bilibili视频语音识别工具环境...")
    print("=" * 50)
    
    # 测试Python版本
    version_ok = test_python_version()
    
    # 测试Python库
    packages_ok = test_python_packages()
    
    # 测试外部工具
    tools_ok = test_external_tools()
    
    # 详细测试
    test_torch_details()
    test_funasr_details()
    modelscope_ok = test_modelscope_compatibility()
    
    print("\n" + "=" * 50)
    
    # 总体评估
    all_tests = [version_ok, packages_ok, tools_ok, modelscope_ok]
    if all(all_tests):
        print("🎉 所有环境测试通过！可以运行Bilibili视频语音识别工具。")
        return 0
    else:
        failed_count = sum(1 for x in all_tests if not x)
        print(f"⚠️  {failed_count} 项测试失败，请检查上述错误信息。")
        
        # 提供具体建议
        if not version_ok:
            print("💡 建议: 升级Python到3.8或更高版本")
        if not packages_ok:
            print("💡 建议: 重新安装缺失的Python包")
        if not tools_ok:
            print("💡 建议: 安装缺失的外部工具")
        if not modelscope_ok:
            print("💡 建议: 升级Python到3.9或使用兼容的modelscope版本")
            
        return 1

if __name__ == "__main__":
    sys.exit(main())