# 小红书图文发布工具包

这是一个基于 Playwright 的自动化工具，用于将图文笔记发布到小红书（xiaohongshu.com）。

## 📦 项目结构

```
xiaohongshu-publisher/
├── README.md                           # 使用说明
├── requirements.txt                    # Python 依赖
├── conf.py                             # 配置文件
├── upload_image_note_to_xiaohongshu.py # 主程序
├── get_xiaohongshu_cookie.py          # Cookie 获取工具
├── utils/
│   ├── __init__.py
│   ├── log.py                         # 日志模块
│   ├── base_social_media.py           # 基础工具
│   └── stealth.min.js                 # 反检测脚本
└── cookies/                           # Cookie 存储目录
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 配置 Chrome 路径

编辑 `conf.py` 文件，设置你的 Chrome 浏览器路径：

```python
# macOS 默认路径
LOCAL_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Windows 示例路径
LOCAL_CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"

# Linux 示例路径
LOCAL_CHROME_PATH = "/usr/bin/google-chrome"
```

### 3. 获取小红书 Cookie

```bash
python get_xiaohongshu_cookie.py
```

运行后会自动打开浏览器，请扫码登录小红书创作者平台。登录成功后，cookie 将保存在 `cookies/xiaohongshu_uploader/account.json`。

### 4. 发布图文笔记

#### 命令行方式

```bash
# 发布单张图片
python upload_image_note_to_xiaohongshu.py \
  --title "我的第一条小红书笔记 🎉" \
  --content "今天开始尝试自动化发布！\n\n#自动化 #小红书" \
  --images "/path/to/image.jpg"

# 发布多张图片（最多9张）
python upload_image_note_to_xiaohongshu.py \
  --title "多张图片测试" \
  --content "这是多张图片的笔记\n\n可以添加换行" \
  --images "/path/to/image1.jpg" "/path/to/image2.jpg"

# 定时发布
python upload_image_note_to_xiaohongshu.py \
  --title "定时发布的笔记" \
  --content "这条笔记将在指定时间发布" \
  --images "/path/to/image.jpg" \
  --publish-time "2025-02-10 15:30"
```

#### Python 函数调用

```python
import asyncio
from pathlib import Path
from upload_image_note_to_xiaohongshu import XiaoHongShuImageNote

async def publish():
    note = XiaoHongShuImageNote(
        title="测试笔记 📝",
        content="这是通过 Python 发布的笔记内容\n\n支持换行！",
        images=[Path("/path/to/image.jpg")],
        tags=["自动化", "Python"],
        account_file=Path("cookies/xiaohongshu_uploader/account.json")
    )
    await note.main()

asyncio.run(publish())
```

## 📋 命令行参数说明

| 参数 | 说明 | 必填 |
|------|------|------|
| `--title` | 笔记标题（最多30字） | 是 |
| `--content` | 笔记正文内容 | 是 |
| `--images` | 图片路径列表（支持多张，空格分隔） | 是 |
| `--tags` | 话题标签列表（空格分隔） | 否 |
| `--publish-time` | 定时发布时间（格式：YYYY-MM-DD HH:MM） | 否 |
| `--account-file` | Cookie 文件路径 | 否 |

## 🔧 OpenClaw Skill 使用

如果你使用 OpenClaw，可以将 `SKILL.md` 放入你的 skills 目录：

```bash
# 复制 skill 文件到 OpenClaw skills 目录
cp SKILL.md ~/.openclaw/workspace/skills/xiaohongshu-publisher/
```

然后在 OpenClaw 中就可以通过自然语言指令发布笔记：

```
发布一篇小红书笔记，标题是"今日份工作小结"，内容是"完成了很多工作！"，图片是 /tmp/work.png
```

## ⚠️ 注意事项

1. **Cookie 有效期**：小红书 Cookie 会过期，需要定期重新获取
2. **发布频率限制**：小红书有发布频率限制，建议不要过于频繁
3. **图片规格**：建议使用 3:4 或 1:1 比例图片
4. **内容规范**：遵守小红书社区规范，避免违规内容
5. **网络环境**：需要能够访问 creator.xiaohongshu.com

## 🐛 故障排除

### 无法找到 Chrome

确保 `conf.py` 中的 `LOCAL_CHROME_PATH` 指向正确的 Chrome 可执行文件。

### Cookie 失效

运行 `python get_xiaohongshu_cookie.py` 重新获取 Cookie。

### 图片上传失败

- 检查图片路径是否正确
- 确保图片文件存在且可读
- 单张图片建议不超过 20MB

### 发布超时

- 检查网络连接
- 确认能够访问小红书创作者平台
- 尝试增加等待时间

## 📄 许可证

MIT License - 自由使用和修改

## 🙏 致谢

本项目基于 Playwright 和 social-auto-upload 项目构建。
