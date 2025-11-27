# B站 Cookie 获取指南

## 为什么需要 Cookie？

- **普通视频**：不需要 Cookie，但画质可能限制在 480P/720P
- **高清视频（1080P+）**：需要登录账号（Cookie）
- **大会员视频**：需要大会员账号的 Cookie
- **部分受限视频**：需要登录才能观看

## 获取 Cookie 的方法

### 方法1：使用浏览器插件（推荐）

1. **安装插件**：
   - Chrome/Edge: 搜索 "Get cookies.txt LOCALLY" 或 "cookies.txt"
   - Firefox: 搜索 "cookies.txt" 插件

2. **导出 Cookie**：
   - 登录 B站 (bilibili.com)
   - 点击插件图标
   - 选择导出为 Netscape 格式
   - 保存为 `bilibili_cookies.txt`

### 方法2：使用开发者工具（手动）

1. **打开 B站并登录**：https://www.bilibili.com

2. **打开开发者工具**：
   - 按 F12 或右键 → 检查

3. **获取 Cookie**：
   - 切换到 "Network" (网络) 标签
   - 刷新页面
   - 点击任意请求
   - 在 Headers 中找到 "Cookie" 字段
   - 复制整个 Cookie 值

4. **创建 Cookie 文件**：
   创建 `bilibili_cookies.txt` 文件，格式如下：
   ```
   # Netscape HTTP Cookie File
   .bilibili.com	TRUE	/	FALSE	0	SESSDATA	你的SESSDATA值
   .bilibili.com	TRUE	/	FALSE	0	bili_jct	你的bili_jct值
   .bilibili.com	TRUE	/	FALSE	0	DedeUserID	你的DedeUserID值
   ```

### 方法3：使用 yt-dlp 自动提取（最简单）

```bash
# 激活环境
conda activate bilibili_dl

# 从浏览器自动提取 Cookie（需要先登录 B站）
yt-dlp --cookies-from-browser chrome --cookies bilibili_cookies.txt https://www.bilibili.com

# 或者从 Edge 浏览器
yt-dlp --cookies-from-browser edge --cookies bilibili_cookies.txt https://www.bilibili.com

# 或者从 Firefox 浏览器
yt-dlp --cookies-from-browser firefox --cookies bilibili_cookies.txt https://www.bilibili.com
```

## 使用 Cookie

将 `bilibili_cookies.txt` 文件放在脚本同一目录下，脚本会自动检测并使用。

## 安全提示

⚠️ **重要**：
- Cookie 包含你的登录信息，不要分享给他人
- 不要上传到公开的代码仓库
- 定期更新 Cookie（通常 Cookie 会过期）
- 建议将 `bilibili_cookies.txt` 添加到 `.gitignore`

## 测试 Cookie 是否有效

```bash
conda activate bilibili_dl
yt-dlp --cookies bilibili_cookies.txt -F https://www.bilibili.com/video/BV1T2k6BaEeC
```

如果能看到 1080P 及以上画质选项，说明 Cookie 有效。
