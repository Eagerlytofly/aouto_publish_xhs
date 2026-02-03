# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime
from pathlib import Path
import random
import argparse

from playwright.async_api import Playwright, async_playwright, Page

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS, BASE_DIR
from utils.base_social_media import set_init_script
from utils.log import xiaohongshu_logger
# from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags  # 如果需要可取消注释


async def cookie_auth(account_file: Path) -> bool:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=str(account_file))
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=5000)
        except:
            print("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


async def xiaohongshu_setup(account_file: Path, handle=False) -> bool:
    if not account_file.exists() or not await cookie_auth(account_file):
        if not handle:
            return False
        xiaohongshu_logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录')
        # await xiaohongshu_cookie_gen(account_file)  # 如果有登录逻辑可启用
        return False
    return True


class XiaoHongShuImageNote:
    def __init__(
        self,
        title: str,
        content: str,
        images: list[Path | str],
        tags: list[str] = None,
        publish_date: datetime | int = 0,
        account_file: Path = None,
        thumbnail_path: str = None
    ):
        self.title = title
        self.content = content.strip()
        self.images = [Path(p) if isinstance(p, str) else p for p in images] if images else []
        self.tags = tags or []
        self.publish_date = publish_date
        self.account_file = account_file
        self.thumbnail_path = thumbnail_path
        self.headless = LOCAL_CHROME_HEADLESS
        self.local_executable_path = LOCAL_CHROME_PATH

    async def set_schedule_time(self, page: Page, publish_date: datetime):
        xiaohongshu_logger.info("  [-] 正在设置定时发布时间...")
        label = page.locator("label:has-text('定时发布')")
        if await label.count():
            await label.click()
            await asyncio.sleep(1)

        datetime_input = page.get_by_placeholder("选择日期和时间") or \
                         page.locator('.semi-input[placeholder*="日期和时间"]')
        if await datetime_input.count():
            await datetime_input.click()
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.type(publish_date.strftime("%Y-%m-%d %H:%M"))
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)

    async def upload(self, playwright: Playwright):
        browser = await playwright.chromium.launch(
            headless=self.headless,
            executable_path=self.local_executable_path if self.local_executable_path else None
        )
        context = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            storage_state=str(self.account_file)
        )
        context = await set_init_script(context)
        page = await context.new_page()

        url = "https://creator.xiaohongshu.com/publish/publish?source=official&from=menu&target=image"
        await page.goto(url)
        xiaohongshu_logger.info(f'[+] 正在创建图文笔记 ------- {self.title}')
        
        await asyncio.sleep(5)

        # 1. 上传图片
        if self.images:
            xiaohongshu_logger.info(f"  [-] 上传 {len(self.images)} 张图片...")
            upload_input = page.locator('input[type="file"][multiple]') or \
                           page.locator('div.upload-area input[type="file"]') or \
                           page.locator('input.upload-input')
            if await upload_input.count():
                await upload_input.set_input_files([str(p) for p in self.images if p.exists()])
                await asyncio.sleep(2)
                try:
                    await page.wait_for_selector('div[class*="preview"] img, img[src*="image"]', timeout=60000)
                    xiaohongshu_logger.info("[+] 图片预览加载完成")
                except:
                    xiaohongshu_logger.warning("未检测到图片预览，但继续...")
            else:
                xiaohongshu_logger.warning("未找到图片上传 input，跳过上传")

        # 2. 填充标题
        xiaohongshu_logger.info("  [-] 正在填充标题...")
        title_input = page.get_by_placeholder("填写标题会有更多赞哦～") or \
                      page.get_by_role("textbox", name="填写标题会有更多赞哦～") or \
                      page.locator('input[placeholder*="填写标题"]')

        if await title_input.count() > 0:
            await title_input.fill("")
            await title_input.fill(self.title[:30])
            await title_input.press("Enter")
        else:
            xiaohongshu_logger.warning("标题输入框未找到，使用 fallback")
            await page.click('div.title-container')
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            await page.keyboard.type(self.title[:30])

        await asyncio.sleep(1 + random.uniform(0, 1))

        # 3. 填充正文
        xiaohongshu_logger.info("  [-] 正在填充正文...")

        content_selectors = [
            'div[contenteditable="true"][data-placeholder*="想法"], div[contenteditable="true"][placeholder*="想法"]',
            'div[contenteditable="true"]:not([class*="title"]):not([class*="tag"])',
            '.semi-input-textarea, .semi-editor [contenteditable]',
            '.editor-content, .note-content [contenteditable]',
            'div[class*="editor"] [contenteditable="true"]',
            '.ql-editor'
        ]

        content_area = None
        for sel in content_selectors:
            loc = page.locator(sel)
            if await loc.count() > 0 and await loc.is_visible():
                content_area = loc.first
                xiaohongshu_logger.info(f"[+] 找到正文编辑器，使用 selector: {sel}")
                break

        if content_area:
            await content_area.click(force=True)
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            
            lines = self.content.split('\n')
            for i, line in enumerate(lines):
                await content_area.press_sequentially(line.strip(), delay=40)
                if i < len(lines) - 1:
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(0.5 + random.uniform(0, 0.8))
        else:
            xiaohongshu_logger.error("所有正文 selector 都找不到！")
            await page.screenshot(path="content_editor_fail.png")

        # 4. 添加话题
        if self.tags:
            xiaohongshu_logger.info(f"  [-] 添加 {len(self.tags)} 个话题...")
            await content_area.press_sequentially("\n\n", delay=50)
            for tag in self.tags:
                await content_area.press_sequentially("#" + tag + " ", delay=60)
                await asyncio.sleep(0.5 + random.uniform(0, 0.8))

        # 5. 定时发布
        if self.publish_date and self.publish_date != 0 and isinstance(self.publish_date, datetime):
            await self.set_schedule_time(page, self.publish_date)

        # 6. 点击发布
        xiaohongshu_logger.info("  [-] 准备发布...")
        publish_btn_text = "定时发布" if self.publish_date != 0 else "发布"
        while True:
            try:
                btn = page.locator(f'button:has-text("{publish_btn_text}")')
                await btn.click()
                await page.wait_for_url("https://creator.xiaohongshu.com/publish/success*", timeout=5000)
                xiaohongshu_logger.success("  [-] 图文笔记发布成功！")
                break
            except:
                xiaohongshu_logger.info("  [-] 发布中... 等待跳转")
                await asyncio.sleep(1)
                await page.screenshot(path="publish_wait.png")

        await context.storage_state(path=str(self.account_file))
        xiaohongshu_logger.success('  [-] cookie 更新完毕')
        await asyncio.sleep(2)
        await context.close()
        await browser.close()

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)


def parse_arguments():
    parser = argparse.ArgumentParser(description="小红书图文笔记自动发布工具")
    parser.add_argument("--title", type=str, required=True, help="笔记标题")
    parser.add_argument("--content", type=str, required=True, help="笔记正文（支持多行，用引号包裹）")
    parser.add_argument("--images", type=str, nargs="*", default=[], help="图片路径列表（空格分隔，支持多个）")
    parser.add_argument("--tags", type=str, nargs="*", default=[], help="话题标签列表（空格分隔）")
    parser.add_argument("--publish-time", type=str, default="0", help="发布时间，格式 YYYY-MM-DD HH:MM，默认为0（立即发布）")
    parser.add_argument("--account-file", type=str, default=str(Path(BASE_DIR) / "cookies" / "xiaohongshu_uploader" / "account.json"), help="cookie 文件路径")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    account_file = Path(args.account_file)
    asyncio.run(xiaohongshu_setup(account_file, handle=True))

    # 处理发布时间
    if args.publish_time == "0":
        publish_date = 0
    else:
        try:
            publish_date = datetime.strptime(args.publish_time, "%Y-%m-%d %H:%M")
        except ValueError:
            print("发布时间格式错误，应为 YYYY-MM-DD HH:MM，已默认立即发布")
            publish_date = 0

    note = XiaoHongShuImageNote(
        title=args.title,
        content=args.content,
        images=args.images,
        tags=args.tags,
        publish_date=publish_date,
        account_file=account_file
    )

    asyncio.run(note.main())