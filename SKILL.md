---
name: video-summarizer
description: "一键总结视频内容。用户丢一个视频链接，自动提取字幕/转录音频并通过模型整理成结构化摘要。Trigger: 总结这个视频, 帮我整理一下这个视频, 看看这个视频讲了什么, 丢 Bilibili/YouTube 等链接并要求总结视频内容, 视频总结, video summarize, summarize this video. Do NOT trigger: 普通视频生成请求, 与视频内容无关的简单问答, 非视频链接。兼容 DSharness、HanaAgent、workbuddy 等多 agent 框架。"
default-enabled: false
---

# Video Summarizer Skill

一键总结视频内容。用户丢一个视频链接过来，自动提取字幕/转录音频并通过模型整理成结构化摘要。

## When to Use

Trigger when the user:
- Shares a video link (any platform) and asks you to summarize it
- Says "总结这个视频", "帮我整理一下这个视频", "看看这个视频讲了什么"
- Pastes a video URL and says "总结" or similar keywords
- Drops a Bilibili / YouTube / other platform link and expects a content summary

Do NOT trigger for:
- General video generation requests
- Simple Q&A not about video content
- Non-video links

## Workflow

When triggered, the agent should:

1. **Locate & run the summary script**: The script ships with this skill at `scripts/video-summary.py`, relative to this `SKILL.md`. Run it from the skill root directory (no hard-coded filesystem path is required):

   ```
   # 默认 turbo 模型（识别率高，首次需下载 ~1.5GB）
   python scripts/video-summary.py <video-url>
   # 指定更快的模型
   python scripts/video-summary.py <video-url> base
   # 反爬平台（B站/抖音/YouTube 等）带 cookies 文件
   python scripts/video-summary.py <video-url> --cookies cookies.txt
   ```

   If the host framework exposes the skill directory as a variable (e.g. `${SKILL_DIR}`), resolve the script through it; otherwise cd into this skill folder first. This handles platform detection (Bilibili needs custom Referer header), subtitle extraction, audio download, and Whisper transcription.

   **Model selection**: `base` 快但精度一般，`turbo` 慢但精度最高。约 7 分钟视频：base ~3min，turbo ~10-15min。不指定时默认 `turbo`。

2. **Organize the result**: The script outputs JSON with a `summary_prompt` field containing the raw transcript. The agent reads the transcript and produces a structured summary in this format:
   - **标题与来源**
   - **核心内容概览** (2-3 sentences)
   - **关键要点** (numbered, each with brief explanation)
   - **值得注意的细节/金句** (if any)

## Cookies 注意事项（重要）

大多数主流平台（B站、YouTube、抖音、TikTok、小红书、Vimeo 等）现在需要 cookies 才能通过反爬。脚本会：
1. 优先使用 `--cookies cookies.txt` 显式传入的 Netscape 格式 cookies 文件
2. 没有显式文件时自动探测 Chrome / Edge / Firefox 浏览器 cookies（`yt-dlp --cookies-from-browser`）

注意：新版 Chrome/Edge 的加密 cookie 常导致 `--cookies-from-browser` 提取失败（DPAPI 报错），所以遇到反爬失败时，优先准备 cookies.txt 文件：
- 浏览器装 "Get cookies.txt LOCALLY" 类扩展，登录目标平台后导出
- 传参：`python scripts/video-summary.py <url> --cookies cookies.txt`

## Environment Status

All dependencies are installed and ready:
- `yt-dlp` (2026.08.19) - installed, working
- `ffmpeg` - globally available in PATH
- `openai-whisper` (v20250625) - installed, `base` model cached at 138.5 MB
- Python script ships with this skill at `scripts/video-summary.py` (resolve relative to this SKILL.md)

## Notes

- Bilibili videos without user/auto subtitles will fall back to audio transcription (slower but works)
- YouTube with auto-captions is fastest (no audio download needed)
- Script timeout set to 900s for long videos; most 20-min videos complete within 2-3 min total
- The agent should present the final summary directly in chat, not just the raw JSON