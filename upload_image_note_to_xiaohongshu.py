# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime
from pathlib import Path
import random
import argparse
import re

from playwright.async_api import async_playwright, Page, TimeoutError, expect

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS, BASE_DIR
from utils.base_social_media import set_init_script
from utils.log import xiaohongshu_logger
# from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags  # 如需使用可取消注释


async def cookie_auth(account_file: Path) -> bool:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=str(account_file))
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=8000)
        except TimeoutError:
            xiaohongshu_logger.warning("[+] cookie 可能失效（等待超时）")
            await context.close()
            await browser.close()
            return False
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            xiaohongshu_logger.warning("[+] 检测到登录页，cookie 失效")
            return False
        xiaohongshu_logger.info("[+] cookie 有效")
        await context.close()
        await browser.close()
        return True


async def xiaohongshu_setup(account_file: Path, handle=False) -> bool:
    if not account_file.exists() or not await cookie_auth(account_file):
        if not handle:
            return False
        xiaohongshu_logger.info('[+] cookie 文件不存在或失效，即将打开浏览器手动登录（扫码/短信）')
        # await xiaohongshu_cookie_gen(account_file)  # 如有登录函数可启用
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
        thumbnail_path: str = None,
        headless: bool = LOCAL_CHROME_HEADLESS,  # 可通过参数覆盖
    ):
        self.title = title.strip()
        self.content = content.strip()
        self.images = [Path(p) if isinstance(p, str) else p for p in images] if images else []
        self.tags = tags or []
        self.publish_date = publish_date
        self.account_file = account_file
        self.thumbnail_path = thumbnail_path
        self.headless = headless
        self.local_executable_path = LOCAL_CHROME_PATH

    async def set_schedule_time(self, page: Page, publish_date: datetime):
        xiaohongshu_logger.info("  [-] 设置定时发布...")
        try:
            schedule_label = page.locator('label:has-text("定时发布"), label[for*="schedule"], [aria-label*="定时"]')
            if await schedule_label.count():
                await schedule_label.click(delay=150)
                await asyncio.sleep(1.2 + random.uniform(0, 0.8))

            time_input = (
                page.get_by_placeholder("选择日期和时间") or
                page.get_by_placeholder(re.compile(r"日期|时间")) or
                page.locator('input[placeholder*="日期"], input[type="datetime-local"], [aria-label*="发布时间"]')
            )
            if await time_input.count():
                await time_input.click(delay=200)
                await time_input.press("Control+A")
                await time_input.type(publish_date.strftime("%Y-%m-%d %H:%M"), delay=60)
                await time_input.press("Enter", delay=150)
                xiaohongshu_logger.info("[+] 定时时间设置成功")
            else:
                xiaohongshu_logger.warning("未找到定时输入框，跳过")
        except Exception as e:
            xiaohongshu_logger.warning(f"定时设置异常（可忽略）：{e}")

    async def upload(self, playwright):
        browser = await playwright.chromium.launch(
            headless=self.headless,
            executable_path=self.local_executable_path if self.local_executable_path else None,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1600, "height": 1000},
            storage_state=str(self.account_file),
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        context = await set_init_script(context)
        page = await context.new_page()

        url = "https://creator.xiaohongshu.com/publish/publish?source=official&from=menu&target=image"
        await page.goto(url, wait_until="networkidle", timeout=45000)
        xiaohongshu_logger.info(f'[+] 进入发布页 ------- {self.title}')
        
        await asyncio.sleep(4 + random.uniform(1, 3))

        # 1. 上传图片
        if self.images:
            xiaohongshu_logger.info(f"  [-] 上传 {len(self.images)} 张图片...")
            upload_input = (
                page.locator('input[type="file"][multiple], input[type="file"]') or
                page.get_by_role("button", name=re.compile(r"上传|图片|添加")) or
                page.locator('[aria-label*="上传图片"], [aria-label*="添加图片"]')
            )
            files = [str(p) for p in self.images if p.exists()]
            if await upload_input.count() and files:
                await upload_input.set_input_files(files, timeout=30000)
                await asyncio.sleep(3 + random.uniform(1, 4))
                try:
                    await page.wait_for_selector('img[src*="image"], div[class*="preview"] img', timeout=80000)
                    xiaohongshu_logger.info("[+] 图片上传 & 预览完成")
                except TimeoutError:
                    xiaohongshu_logger.warning("图片预览未及时出现，继续...")
            else:
                xiaohongshu_logger.warning("未找到上传 input/button，检查页面")

        # 2. 填充标题
        xiaohongshu_logger.info("  [-] 填充标题...")
        title_locators = [
            page.get_by_placeholder("填写标题会有更多赞哦"),
            page.get_by_placeholder("填写标题会有更多赞哦～"),
            page.get_by_placeholder("填写标题"),
            page.get_by_placeholder("笔记标题"),
            page.get_by_placeholder(re.compile(r"标题|赞哦")),
            page.locator('input.d-text[type="text"][placeholder*="标题"]'),
            page.locator('input[placeholder*="标题"]'),
            page.locator('[aria-label*="标题"] input, [aria-label*="标题"]'),
        ]

        title_input = None
        for loc in title_locators:
            try:
                await expect(loc).to_be_visible(timeout=6000)
                title_input = loc.first
                xiaohongshu_logger.info(f"[+] 标题定位成功")
                break
            except Exception:
                continue

        if title_input is None:
            xiaohongshu_logger.warning("所有预设 locator 失败，进入 placeholder 扫描模式")
            all_text_inputs = page.locator('input[type="text"], input:not([type])')
            count = await all_text_inputs.count()
            for i in range(min(count, 8)):
                inp = all_text_inputs.nth(i)
                try:
                    await expect(inp).to_be_visible(timeout=3000)
                    ph = await inp.get_attribute("placeholder") or ""
                    if "标题" in ph or "赞哦" in ph or "title" in ph.lower():
                        title_input = inp
                        xiaohongshu_logger.info(f"[+] 通过扫描找到标题输入框 (placeholder: {ph})")
                        break
                except:
                    continue

        if title_input:
            await title_input.click(delay=150)
            await title_input.fill(self.title[:30], timeout=15000)
            await title_input.press("Enter", delay=100)
            xiaohongshu_logger.info("[+] 标题填充成功")
        else:
            xiaohongshu_logger.error("标题输入框彻底定位失败")
            await page.screenshot(path=f"title_fail_{datetime.now():%Y%m%d_%H%M%S}.png")

        await asyncio.sleep(1.5 + random.uniform(0.5, 1.5))

        # 3. 填充正文
        xiaohongshu_logger.info("  [-] 填充正文...")
        content_selectors = [
            'div[contenteditable="true"][role="textbox"]:not([class*="title"]):not([class*="tag"])',
            'div[contenteditable="true"]:not([aria-hidden="true"]):not([class*="title"])',
            'div.ProseMirror[role="textbox"], div[aria-label*="正文"], div[aria-multiline="true"]',
            'div[contenteditable="true"][data-placeholder*="想法"], .editor [contenteditable]',
            '.ql-editor, .note-editor [contenteditable]',
        ]
        content_area = None
        for sel in content_selectors:
            loc = page.locator(sel)
            try:
                await expect(loc).to_be_visible(timeout=8000)
                content_area = loc.first
                xiaohongshu_logger.info(f"[+] 正文编辑器定位成功：{sel}")
                break
            except:
                continue

        if content_area:
            await content_area.click(position={"x": 30, "y": 30}, force=True, timeout=15000)
            await asyncio.sleep(0.6 + random.uniform(0, 1))

            await content_area.press("Control+KeyA", delay=80)
            await content_area.press("Delete", delay=120)

            lines = [l.strip() for l in self.content.splitlines() if l.strip()]
            for idx, line in enumerate(lines):
                await content_area.press_sequentially(line, delay=random.uniform(35, 85))
                if idx < len(lines) - 1:
                    await content_area.press("Enter", delay=150)
                    await asyncio.sleep(random.uniform(0.7, 1.8))

            if self.tags:
                await content_area.press("Enter", delay=120)
                await content_area.press("Enter", delay=120)
                for tag in self.tags[:6]:
                    await content_area.press_sequentially(f"#{tag} ", delay=random.uniform(55, 110))
                    await asyncio.sleep(0.5 + random.uniform(0.3, 1))

            xiaohongshu_logger.info("[+] 正文 & 话题完成")
        else:
            xiaohongshu_logger.error("正文所有 selector 失败！")
            await page.screenshot(path=f"editor_fail_{datetime.now():%Y%m%d_%H%M%S}.png")

        # 4. 定时发布
        if isinstance(self.publish_date, datetime) and self.publish_date > datetime.now():
            await self.set_schedule_time(page, self.publish_date)

        # 5. 点击发布
        xiaohongshu_logger.info("  [-] 准备发布...")
        btn_text = "定时发布" if self.publish_date else "发布"
        publish_btn = (
            page.get_by_role("button", name=btn_text) or
            page.locator(f'button:has-text("{btn_text}"), button[aria-label*="{btn_text}"]')
        )
        await asyncio.sleep(random.uniform(4, 9))

        try:
            await publish_btn.click(timeout=15000)
            await page.wait_for_url("**/success**", timeout=20000)
            xiaohongshu_logger.success("[+] 笔记发布成功！")
        except Exception as e:
            xiaohongshu_logger.warning(f"发布点击异常：{e}")
            await page.screenshot(path=f"publish_fail_{datetime.now():%Y%m%d_%H%M%S}.png")

        await context.storage_state(path=str(self.account_file))
        xiaohongshu_logger.info('[+] cookie 已更新')
        await context.close()
        await browser.close()

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)


def parse_arguments():
    parser = argparse.ArgumentParser(description="小红书图文笔记自动发布工具")
    parser.add_argument("--title", type=str, required=True, help="笔记标题")
    parser.add_argument("--content", type=str, required=True, help="笔记正文（支持多行）")
    parser.add_argument("--images", type=str, nargs="*", default=[], help="图片路径（空格分隔）")
    parser.add_argument("--tags", type=str, nargs="*", default=[], help="话题标签（空格分隔）")
    parser.add_argument("--publish-time", type=str, default="0", help="定时 YYYY-MM-DD HH:MM，0=立即")
    parser.add_argument("--account-file", type=str, default=str(Path(BASE_DIR) / "cookies" / "xiaohongshu_uploader" / "account.json"))
    parser.add_argument("--headless", action="store_true", help="使用无头模式（默认有头窗口）")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    account_file = Path(args.account_file)
    asyncio.run(xiaohongshu_setup(account_file, handle=True))

    publish_date = 0
    if args.publish_time != "0":
        try:
            publish_date = datetime.strptime(args.publish_time, "%Y-%m-%d %H:%M")
        except ValueError:
            print("发布时间格式错误，默认立即发布")

    note = XiaoHongShuImageNote(
        title=args.title,
        content=args.content,
        images=args.images,
        tags=args.tags,
        publish_date=publish_date,
        account_file=account_file,
        headless=args.headless  # 通过命令行控制：加 --headless 则无头，不加则有窗口
    )

    asyncio.run(note.main())