---
name: video-summarizer
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

1. **Run the summary script**:
   ```
   # 默认 base 模型（快，~140MB）
   python D:\AI\Hanako\skills\video-summarizer\scripts\video-summary.py <video-url>
   # 高精度 turbo 模型（慢，~1.5GB，识别率最高）
   python D:\AI\Hanako\skills\video-summarizer\scripts\video-summary.py <video-url> turbo
   ```
   This handles platform detection (Bilibili needs custom Referer header), subtitle extraction, audio download, and Whisper transcription.

   **Model selection**: When the user doesn't specify, ask "base 还是 turbo？" base 快但精度一般，turbo 慢但精度最高。约 7 分钟视频：base ~3min，turbo ~10-15min。

2. **Organize the result**: The script outputs JSON with a `summary_prompt` field containing the raw transcript. The agent reads the transcript and produces a structured summary in this format:
   - **标题与来源**
   - **核心内容概览** (2-3 sentences)
   - **关键要点** (numbered, each with brief explanation)
   - **值得注意的细节/金句** (if any)

## Environment Status

All dependencies are installed and ready:
- `yt-dlp` - installed, working (Bilibili with Referer header, YouTube with default config)
- `ffmpeg` - globally available in PATH
- `openai-whisper` (v20250625) - installed, `base` model cached at 138.5 MB
- Python script at `D:\AI\Hanako\skills\video-summarizer\scripts\video-summary.py`

## Notes

- Bilibili videos without user/auto subtitles will fall back to audio transcription (slower but works)
- YouTube with auto-captions is fastest (no audio download needed)
- Script timeout set to 900s for long videos; most 20-min videos complete within 2-3 min total
- The agent should present the final summary directly in chat, not just the raw JSON
