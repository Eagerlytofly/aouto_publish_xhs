from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
XHS_SERVER = "http://127.0.0.1:11901"

# 修改为你的 Chrome 浏览器路径
# macOS 示例:
LOCAL_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Windows 示例:
# LOCAL_CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe"

# Linux 示例:
# LOCAL_CHROME_PATH = "/usr/bin/google-chrome"

# 是否使用无头模式（True = 不显示浏览器窗口）
LOCAL_CHROME_HEADLESS = False
