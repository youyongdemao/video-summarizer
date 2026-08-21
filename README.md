# video-summarizer

一键总结视频内容。丢一个视频链接进来，自动提取字幕 / 转录音频，输出结构化摘要数据供 AI Agent 整理成最终总结。

一个为 AI 助手（ DSherness、workbuddy、HanaAgent 等）设计的 agent skill：`SKILL.md` 描述触发条件与工作流，`scripts/video-summary.py` 负责下载与转录。

## 功能

- 平台检测：Bilibili、YouTube、抖音（Douyin）、小红书、微博，其余交给 yt-dlp 的通用提取器
- 优先尝试字幕（Bilibili 需 Referer；YouTube 自动字幕最快）
- 无字幕时自动降级为 Whisper 转录音频
- Bilibili / 抖音等反爬平台自动携带浏览器 cookies
- 输出 JSON：`metadata`（标题/UP主/时长）+ `transcript`（转录全文）+ `summary_prompt`（预组装好的总结提示词）

## 用法

```bash
# 默认 turbo 模型（识别率高，首次需下载 ~1.5GB）
python scripts/video-summary.py <video-url>

# 指定更快的模型
python scripts/video-summary.py <video-url> base     # 快，~140MB
python scripts/video-summary.py <video-url> small
python scripts/video-summary.py <video-url> medium
python scripts/video-summary.py <video-url> turbo    # 默认，最准
```

Agent 读取输出 JSON 中的 `summary_prompt`，按以下结构产出最终总结：

- 标题与来源
- 核心内容概览（2-3 句）
- 关键要点（编号，各附简述）
- 值得注意的细节 / 金句（如有）

## 依赖

- Python 3.8+
- `yt-dlp`
- `ffmpeg`（PATH 中可用）
- `openai-whisper`（`pip install openai-whisper`）

## 已知限制

- 抖音反爬较严：脚本会尝试读取 Chrome / Edge / Firefox 的 cookies（`yt-dlp --cookies-from-browser`）。若浏览器未登录抖音或 cookies 加密无法解密（新版 Chrome 的 DPAPI 问题），下载可能失败
- 无字幕视频走 Whisper 转录，时长与音频质量直接影响耗时；20 分钟以内的视频通常 2-15 分钟内完成（base 快，turbo 慢）
- 脚本超时上限 900 秒，长视频建议分段

## 许可

MIT
