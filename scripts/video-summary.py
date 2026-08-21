#!/usr/bin/env python3
"""
Video Summarizer - 一键提取视频内容并输出结构化摘要数据

用法:
    python video-summary.py <video-url>

输出:
    JSON 格式，包含 transcript（转录文本）和 metadata（视频元信息），
    供 Agent 读取后进行结构化总结。

支持的平台:
    - Bilibili (字幕优先，无字幕时 Whiser 转录音频)
    - YouTube (优先自动字幕)
    - 其他 yt-dlp 支持的平台
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run_cmd(cmd, timeout=600, stderr_ok=True):
    """Run a command and return stdout/stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1


def detect_platform(url):
    """Detect video platform from URL."""
    url_lower = url.lower()
    if "bilibili.com" in url_lower or "b23.tv" in url_lower:
        return "bilibili"
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    if "douyin.com" in url_lower or "v.douyin.com" in url_lower or "iesdouyin.com" in url_lower:
        return "douyin"
    if "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
        return "xiaohongshu"
    if "weibo.com" in url_lower:
        return "weibo"
    return "generic"


_cookie_args_cache = None

def get_cookie_args():
    """Try to extract cookies from browsers, return yt-dlp cookie args.

    Result is cached so the (slow) browser probe only runs once per process.
    """
    global _cookie_args_cache
    if _cookie_args_cache is not None:
        return _cookie_args_cache
    browsers = ["chrome", "edge", "firefox"]
    for browser in browsers:
        _, stderr, rc = run_cmd(
            f'yt-dlp --no-update --cookies-from-browser {browser} --skip-download '
            f'--print filename "https://www.example.com"',
            timeout=15,
        )
        if rc == 0:
            _cookie_args_cache = ["--cookies-from-browser", browser]
            return _cookie_args_cache
    _cookie_args_cache = []
    return []


def get_platform_args(platform):
    """Return (cookie_args, extra_args) for the given platform.

    Bilibili needs a Referer header; Douyin/TikTok and other anti-scraping
    platforms need browser cookies (fresh anonymous cookies get rejected).
    """
    cookie_needing = {"douyin", "tiktok", "twitter", "instagram", "facebook", "netflix", "kuaishou"}
    if platform == "bilibili":
        return get_cookie_args(), ["--referer", "https://www.bilibili.com/"]
    if platform in cookie_needing:
        return get_cookie_args(), []
    return [], []


def try_get_subtitles(url, platform, work_dir):
    """Try to download subtitles. Returns path to subtitle file or None."""
    cookie_args, extra_args = get_platform_args(platform)

    # For YouTube, prefer auto-subs
    sub_lang = "--write-auto-subs" if platform == "youtube" else "--write-subs"
    sub_format = "--sub-format" 
    
    cmd = [
        "yt-dlp", "--no-update",
        "--skip-download",
        "--write-subs", "--write-auto-subs",
        "--sub-lang", "zh-Hans,zh-CN,zh,en,zh-Hant",
        "--convert-subs", "vtt",
        "-o", f"{work_dir}/%(id)s.%(ext)s",
    ] + cookie_args + extra_args + [url]

    stdout, stderr, rc = run_cmd(" ".join(cmd), timeout=120)

    # Check for downloaded subtitle files
    subtitle_files = list(Path(work_dir).glob("*.vtt"))
    if subtitle_files:
        return str(subtitle_files[0])
    
    # Also check .srt
    subtitle_files = list(Path(work_dir).glob("*.srt"))
    if subtitle_files:
        return str(subtitle_files[0])

    return None


def download_audio(url, platform, work_dir):
    """Download audio only. Returns path to audio file."""
    cookie_args, extra_args = get_platform_args(platform)

    audio_path = os.path.join(work_dir, "audio")

    cmd = [
        "yt-dlp", "--no-update",
        "-f", "worstaudio[ext=m4a]/worstaudio/bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "64K",
        "-o", f"{audio_path}.%(ext)s",
    ] + cookie_args + extra_args + [url]

    stdout, stderr, rc = run_cmd(" ".join(cmd), timeout=300)

    # Find the downloaded audio file
    for ext in [".mp3", ".m4a", ".opus", ".webm"]:
        candidate = audio_path + ext
        if os.path.exists(candidate):
            return candidate

    # Check any audio file in the temp dir
    for f in Path(work_dir).glob("audio*"):
        if f.suffix in [".mp3", ".m4a", ".opus", ".webm"]:
            return str(f)

    # Try yt-dlp's own output path
    for f in Path(work_dir).glob("*"):
        if f.suffix in [".mp3", ".m4a", ".opus", ".webm"]:
            return str(f)

    print(f"[ERROR] Failed to download audio. yt-dlp stderr:\n{stderr}", file=sys.stderr)
    return None


def extract_text_from_vtt(vtt_path):
    """Extract plain text from VTT subtitle file."""
    import re
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Remove VTT headers and timestamps
    lines = content.split("\n")
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}", line) or re.match(r"^\d+$", line):
            continue
        if line.startswith("NOTE"):
            continue
        text_lines.append(line)
    return " ".join(text_lines)


def transcribe_audio(audio_path, model_name="base"):
    """Transcribe audio using Whisper.
    
    model_name: 'base' (fast, ~140MB) or 'turbo' (accurate, ~1.5GB)
    """
    import whisper
    import warnings
    warnings.filterwarnings("ignore")

    print(f"[Whisper] Transcribing {audio_path} with {model_name} model...", file=sys.stderr)
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, language="zh")
    return result["text"]


def get_metadata(url, platform):
    """Get video metadata."""
    cookie_args, extra_args = get_platform_args(platform)

    cmd = [
        "yt-dlp", "--no-update",
        "--dump-json",
    ] + cookie_args + extra_args + [url]

    stdout, stderr, rc = run_cmd(" ".join(cmd), timeout=60)
    if rc == 0 and stdout:
        try:
            meta = json.loads(stdout)
            return {
                "title": meta.get("title", "Unknown"),
                "uploader": meta.get("uploader") or meta.get("channel", "Unknown"),
                "duration": meta.get("duration", 0),
                "url": meta.get("webpage_url", url),
                "platform": platform,
            }
        except json.JSONDecodeError:
            pass
    
    return {
        "title": "Unknown",
        "uploader": "Unknown",
        "duration": 0,
        "url": url,
        "platform": platform,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: video-summary.py <video-url> [--model base|turbo]"}, ensure_ascii=False))
        sys.exit(1)

    # Parse arguments
    url = None
    model_name = "turbo"
    for arg in sys.argv[1:]:
        if arg == "--model":
            continue
        if arg in ("base", "turbo", "small", "medium", "large"):
            model_name = arg
        elif not url:
            url = arg

    if not url:
        print(json.dumps({"error": "No URL provided"}, ensure_ascii=False))
        sys.exit(1)
    platform = detect_platform(url)

    print(f"[Video Summarizer] Platform: {platform}, URL: {url}", file=sys.stderr)

    with tempfile.TemporaryDirectory(prefix="video_summary_") as work_dir:
        print(f"[Video Summarizer] Working directory: {work_dir}", file=sys.stderr)

        # Step 1: Get metadata
        print("[Video Summarizer] Step 1: Getting metadata...", file=sys.stderr)
        metadata = get_metadata(url, platform)

        # Step 2: Try subtitles first
        print("[Video Summarizer] Step 2: Trying subtitles...", file=sys.stderr)
        transcript = None
        sub_path = try_get_subtitles(url, platform, work_dir)

        if sub_path:
            print(f"[Video Summarizer] Found subtitles: {sub_path}", file=sys.stderr)
            if sub_path.endswith(".vtt"):
                transcript = extract_text_from_vtt(sub_path)
            else:
                with open(sub_path, "r", encoding="utf-8") as f:
                    transcript = f.read()

        # Step 3: If no subtitles, download audio and transcribe
        if not transcript or len(transcript.strip()) < 50:
            print("[Video Summarizer] Step 3: No usable subtitles, downloading audio...", file=sys.stderr)
            audio_path = download_audio(url, platform, work_dir)

            if not audio_path:
                print(json.dumps({
                    "error": "Failed to download audio",
                    "metadata": metadata,
                    "transcript": "",
                    "summary_prompt": f"视频标题：{metadata['title']}\nUP主：{metadata['uploader']}\n时长：{metadata['duration']}秒\n\n（无法获取视频内容）"
                }, ensure_ascii=False))
                sys.exit(1)

            try:
                transcript = transcribe_audio(audio_path, model_name)
            except Exception as e:
                print(f"[ERROR] Whisper transcription failed: {e}", file=sys.stderr)

        # Step 4: Build output
        duration_min = metadata["duration"] // 60
        duration_sec = metadata["duration"] % 60

        summary_prompt = f"""视频标题：{metadata['title']}
UP主/频道：{metadata['uploader']}
时长：{duration_min}分{duration_sec}秒
平台：{platform}

以下是视频的文字内容（来自{'字幕' if sub_path else 'Whisper语音转录'}）：

{transcript if transcript else '(未能获取内容)'}

请根据以上内容生成一份结构化的视频总结。"""

        output = {
            "transcript": transcript or "",
            "metadata": metadata,
            "summary_prompt": summary_prompt,
        }

        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
