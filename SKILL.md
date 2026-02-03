# 小红书图文发布工具（OpenClaw Skill）

自动发布图文笔记到小红书的命令行工具。

## 前置要求

- 已安装 social-auto-upload 项目
- 已配置小红书 cookies
- 网络环境可以访问小红书创作者平台

## 使用方法

### 命令行直接调用

```bash
# 进入项目目录
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate social-auto-upload
cd /Users/wangzhenbo/code/social-auto-upload

# 发布单张图片
python upload_image_note_to_xiaohongshu.py \
  --title "标题" \
  --content "正文内容" \
  --images "/path/to/image.jpg"

# 发布多张图片（空格分隔多个路径）
python upload_image_note_to_xiaohongshu.py \
  --title "标题" \
  --content "正文内容" \
  --images "/path/to/image1.jpg" "/path/to/image2.jpg"
```

### Python 函数调用

```python
import subprocess
from pathlib import Path
from typing import List

def publish_to_xiaohongshu(title: str, content: str, image_paths: List[str]):
    """
    发布图文笔记到小红书
    
    Args:
        title: 笔记标题
        content: 笔记正文（支持换行）
        image_paths: 图片文件路径列表（支持多张）
    
    Returns:
        bool: 发布是否成功
    """
    # 构建图片参数（多个路径用空格分隔）
    images_arg = " ".join([f'"{p}"' for p in image_paths])
    
    cmd = f'''
source /opt/anaconda3/etc/profile.d/conda.sh &&
conda activate social-auto-upload &&
cd /Users/wangzhenbo/code/social-auto-upload &&
python upload_image_note_to_xiaohongshu.py \\
  --title "{title}" \\
  --content "{content}" \\
  --images {images_arg}
'''
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

# 使用示例 - 单张图片
publish_to_xiaohongshu(
    title="今日份工作小结 💼",
    content="今天是充实的一天！✨\\n\\n完成了很多工作！",
    image_paths=["/tmp/work_summary.png"]
)

# 使用示例 - 多张图片
publish_to_xiaohongshu(
    title="长篇总结 📚",
    content="今天的内容比较多...",
    image_paths=["/tmp/page1.png", "/tmp/page2.png"]
)
```

## 命令参数说明

| 参数 | 说明 | 必填 |
|------|------|------|
| `--title` | 笔记标题 | 是 |
| `--content` | 笔记正文内容 | 是 |
| `--images` | 图片文件路径（支持多张，空格分隔） | 是 |
| `--tags` | 话题标签列表（空格分隔） | 否 |
| `--publish-time` | 定时发布时间（格式：YYYY-MM-DD HH:MM） | 否 |

## 内容格式支持

- 标题：支持 emoji
- 内容：支持换行（使用 `\\n`）
- 话题标签：在内容中添加 `#话题标签`
- 多张图片：支持一次上传最多 9 张图片

## 故障排除

### ERR_PROXY_CONNECTION_FAILED
- 检查系统代理设置
- 确认网络可以访问 creator.xiaohongshu.com
- 检查小红书 cookie 是否过期

### ModuleNotFoundError: No module named 'playwright'
- 确保 conda 环境已激活：`conda activate social-auto-upload`
- 或重新安装依赖：`pip install playwright`

## 文件位置

- 项目目录：`/Users/wangzhenbo/code/social-auto-upload`
- 发布脚本：`upload_image_note_to_xiaohongshu.py`
- Cookie 文件：`cookies/xiaohongshu.json`

## 注意事项

1. 发布前请确认 cookie 有效
2. 小红书有发布频率限制，请合理安排
3. 图片尺寸建议 3:4 或 1:1
4. 内容请遵守小红书社区规范
