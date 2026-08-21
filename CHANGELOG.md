# Changelog

## v1.1.1 - 2026-08-21

### 新增

- 仓库新增 `CHANGELOG.md`：内置变更日志，与 GitHub Release notes 同步（Keep a Changelog 风格）

## v1.1.0 - 2026-08-21

### 新增

- 平台检测扩展到 20+ 国内外主流平台（腾讯/爱奇艺/优酷/芒果/西瓜/快手/搜狐/TikTok/Vimeo/Twitch/Twitter/Instagram/Facebook/Netflix 等）
- 新增 `--cookies <file>` 参数：显式传入 Netscape 格式 cookies 文件绕过反爬（最高优先级）
- README 增加平台兼容性实测矩阵

### 优化

- cookies 获取优先级：显式文件 > 浏览器自动探测（Chrome/Edge/Firefox）
- 依赖 yt-dlp 升级至 2026.08.19

### 修复

- 修复 v1.0.0 脚本中重复函数定义问题

## v1.0.0 - 2026-08-21

### 新增

- video-summarizer 首发：一键总结视频内容（字幕提取/Whisper 转录/结构化摘要）
- 平台检测：Bilibili / YouTube / 抖音 / 小红书 / 微博 + yt-dlp 通用提取器
- 字幕优先，无字幕自动 Whisper 转录（base / turbo 可选）
- 反爬平台（Bilibili Referer、抖音等）自动携带浏览器 cookies
- 输出 metadata + transcript + summary_prompt 结构化 JSON
