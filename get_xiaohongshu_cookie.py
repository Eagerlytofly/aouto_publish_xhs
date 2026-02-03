# -*- coding: utf-8 -*-
"""
小红书 Cookie 获取工具
运行后会自动打开浏览器，请扫码登录小红书创作者平台
登录成功后，cookie 将自动保存
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from conf import BASE_DIR, LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS


async def get_xiaohongshu_cookie():
    """获取小红书登录 Cookie"""
    
    # Cookie 保存路径
    account_file = Path(BASE_DIR) / "cookies" / "xiaohongshu_uploader" / "account.json"
    account_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("[*] 正在启动浏览器...")
    print("[*] 请扫码登录小红书创作者平台")
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=LOCAL_CHROME_HEADLESS,
            executable_path=LOCAL_CHROME_PATH if LOCAL_CHROME_PATH else None
        )
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        
        # 打开小红书创作者平台登录页
        await page.goto("https://creator.xiaohongshu.com/login")
        
        print("[*] 请在浏览器中完成登录...")
        print("[*] 登录成功后，按 Enter 键保存 Cookie...")
        
        # 等待用户完成登录
        input()
        
        # 检查是否登录成功
        try:
            await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
            await asyncio.sleep(2)
            
            # 检查是否还在登录页面
            if await page.get_by_text("手机号登录").count() > 0 or \
               await page.get_by_text("扫码登录").count() > 0:
                print("[!] 未检测到登录状态，请重新登录")
                await browser.close()
                return False
            
            # 保存 Cookie
            await context.storage_state(path=str(account_file))
            print(f"[+] Cookie 已保存到: {account_file}")
            print("[+] 现在可以使用 upload_image_note_to_xiaohongshu.py 发布笔记了！")
            
        except Exception as e:
            print(f"[!] 保存 Cookie 时出错: {e}")
        
        await browser.close()
        return True


if __name__ == "__main__":
    asyncio.run(get_xiaohongshu_cookie())
