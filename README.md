# video-summarizer

一键总结视频内容。丢一个视频链接进来，自动提取字幕 / 转录音频，输出结构化摘要数据供 AI Agent 整理成最终总结。

一个为 AI 助手（HanaAgent 等）设计的 Hana skill：`SKILL.md` 描述触发条件与工作流，`scripts/video-summary.py` 负责下载与转录。

## 功能

- 平台检测：Bilibili、YouTube、抖音、TikTok、小红书、微博、腾讯视频、爱奇艺、优酷、芒果TV、西瓜视频、快手、搜狐、Vimeo、Twitch、Twitter/X、Instagram、Facebook、Netflix，其余交给 yt-dlp 的通用提取器
- 优先尝试字幕（Bilibili 需 Referer；YouTube 自动字幕最快）
- 无字幕时自动降级为 Whisper 转录音频（base / turbo 等模型可选）
- 反爬平台自动携带 cookies：显式 `--cookies` 文件优先，其次自动探测 Chrome / Edge / Firefox
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

# 显式传入 cookies 文件（Netscape 格式），绕过反爬
python scripts/video-summary.py <video-url> --cookies cookies.txt
```

Agent 读取输出 JSON 中的 `summary_prompt`，按以下结构产出最终总结：

- 标题与来源
- 核心内容概览（2-3 句）
- 关键要点（编号，各附简述）
- 值得注意的细节 / 金句（如有）

## 平台兼容性（实测，2026-08-21）

| 平台 | 无 cookies | 说明 |
| --- | --- | --- |
| Bilibili | ❌ 需 cookies | HTTP 412 风控，带上浏览器 cookies 即可 |
| YouTube | ❌ 需 cookies | "Sign in to confirm you're not a bot" 验证 |
| 抖音 Douyin | ❌ 需 cookies | 反爬严格，必须 cookies |
| TikTok | ❌ 需 cookies | 与抖音同源反爬 |
| 优酷 Youku | ✅ 可用 | 裸奔可提取 |
| 芒果TV | ✅ 可用 | 裸奔可提取（海外 IP 可能触发地区限制） |
| 腾讯视频 | ✅ 可用（部分） | 免费视频可提取，会员内容需登录 |
| 爱奇艺 | ⚠️ 不稳定 | 部分链接提取失败，建议带 cookies |
| 搜狐 | ⚠️ 不稳定 | 部分链接提取失败 |
| 小红书 | ❌ 需 cookies | 反爬严格 |
| 微博 | ⚠️ 视链接 | 部分视频可提取 |
| Vimeo | ❌ 需登录 | 需账号 cookies |
| Twitch | ⚠️ 视内容 | 公开 VOD/clip 可提取 |
| Twitter/X、Instagram、Facebook、Netflix | ❌ 需登录 | 必须 cookies |

**结论**：绝大多数主流平台需要 cookies。推荐为经常使用的平台准备好 Netscape 格式 cookies 文件，通过 `--cookies` 传入。

### 获取 cookies 文件

1. Chrome / Edge 安装 cookie 导出扩展（如 "Get cookies.txt LOCALLY"）
2. 打开目标平台并登录，点击扩展导出 cookies.txt
3. 传给脚本：`python scripts/video-summary.py <url> --cookies cookies.txt`

脚本也会尝试自动读取浏览器 cookies（`yt-dlp --cookies-from-browser`），但新版 Chrome/Edge 的加密 cookie 常导致提取失败（yt-dlp issue #10927/#7271），因此显式文件更可靠。

## 依赖

- Python 3.8+
- `yt-dlp`（建议 2026.08 之后版本）
- `ffmpeg`（PATH 中可用）
- `openai-whisper`（`pip install openai-whisper`）

## 已知限制

- 无字幕视频走 Whisper 转录，时长与音频质量直接影响耗时；20 分钟以内的视频通常 2-15 分钟内完成（base 快，turbo 慢）
- 脚本超时上限 900 秒，长视频建议分段
- 会员/付费内容即使有 cookies 也可能无法提取

## 许可

MIT
