# B站视频下载工具

使用 Python 下载 B站视频，支持多P（多集）视频。

## 快速开始（推荐）

### Windows 用户

1. **一键设置环境**（首次使用）：
   ```bash
   setup_env.bat
   ```
   这会自动创建 conda 虚拟环境并安装所有依赖。

2. **运行下载**：
   ```bash
   run.bat
   ```

### 手动设置

如果你想手动操作，按以下步骤：

```bash
# 1. 创建 conda 虚拟环境
conda create -n bilibili_dl python=3.10 -y

# 2. 激活环境
conda activate bilibili_dl

# 3. 安装依赖
pip install yt-dlp

# 4. 运行脚本
python download_bilibili.py

# 5. 退出环境（完成后）
conda deactivate
```

## Cookie 配置（可选但推荐）

**为什么需要 Cookie？**
- 不使用 Cookie：只能下载 480P/720P 画质
- 使用 Cookie：可以下载 1080P+ 高清画质，以及会员专享内容

**快速获取 Cookie（推荐方法）：**

```bash
# 1. 先在浏览器登录 B站
# 2. 激活环境
conda activate bilibili_dl

# 3. 从浏览器自动提取 Cookie
yt-dlp --cookies-from-browser chrome --cookies bilibili_cookies.txt https://www.bilibili.com
```

将 `bilibili_cookies.txt` 放在脚本同目录，程序会自动使用。

详细的 Cookie 获取方法请查看 [COOKIE_GUIDE.md](COOKIE_GUIDE.md)

## 使用方法

### 方法1：直接运行脚本

```bash
python download_bilibili.py
```

脚本会自动下载 BV1T2k6BaEeC 的所有分P视频。

### 方法2：修改BV号

编辑 `download_bilibili.py` 文件，修改这一行：

```python
bv_id = 'BV1T2k6BaEeC'  # 改成你想下载的BV号
```

### 方法3：使用命令行直接下载

```bash
# 下载所有分P
yt-dlp --yes-playlist -o "downloads/%(title)s-P%(playlist_index)s.%(ext)s" https://www.bilibili.com/video/BV1T2k6BaEeC

# 只下载特定分P（例如第1集）
yt-dlp --playlist-items 1 -o "downloads/%(title)s.%(ext)s" https://www.bilibili.com/video/BV1T2k6BaEeC

# 下载指定范围（例如第1-5集）
yt-dlp --playlist-items 1-5 -o "downloads/%(title)s-P%(playlist_index)s.%(ext)s" https://www.bilibili.com/video/BV1T2k6BaEeC
```

## 常用选项

- `--yes-playlist`: 下载整个播放列表（所有分P）
- `--no-playlist`: 只下载当前视频
- `--playlist-items 1,3,5`: 下载指定集数
- `--playlist-items 1-10`: 下载指定范围
- `-f best`: 下载最高画质
- `--write-sub`: 下载字幕
- `--embed-subs`: 嵌入字幕到视频

## 输出位置

视频会保存在 `downloads` 目录下。
