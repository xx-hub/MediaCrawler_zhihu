# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/zhihu/login.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。


# -*- coding: utf-8 -*-
import asyncio
import functools
import sys
from typing import Optional

from playwright.async_api import BrowserContext, Page
from tenacity import (RetryError, retry, retry_if_result, stop_after_attempt,
                      wait_fixed)

import config
from base.base_crawler import AbstractLogin
from tools import utils


class ZhiHuLogin(AbstractLogin):

    def __init__(self,
                 login_type: str,
                 browser_context: BrowserContext,
                 context_page: Page,
                 login_phone: Optional[str] = "",
                 cookie_str: str = ""
                 ):
        config.LOGIN_TYPE = login_type
        self.browser_context = browser_context
        self.context_page = context_page
        self.login_phone = login_phone
        self.cookie_str = cookie_str

    @retry(stop=stop_after_attempt(600), wait=wait_fixed(1), retry=retry_if_result(lambda value: value is False))
    async def check_login_state(self) -> bool:
        """
        Check if the current login status is successful and return True otherwise return False
        Returns:

        """
        current_cookie = await self.browser_context.cookies()
        _, cookie_dict = utils.convert_cookies(current_cookie)
        current_web_session = cookie_dict.get("z_c0")
        if current_web_session:
            return True
        return False

    async def begin(self):
        """Start login zhihu"""
        utils.logger.info("[ZhiHu.begin] Begin login zhihu ...")
        if config.LOGIN_TYPE == "qrcode":
            await self.login_by_qrcode()
        elif config.LOGIN_TYPE == "phone":
            await self.login_by_mobile()
        elif config.LOGIN_TYPE == "cookie":
            await self.login_by_cookies()
        else:
            raise ValueError("[ZhiHu.begin]I nvalid Login Type Currently only supported qrcode or phone or cookies ...")

    async def login_by_mobile(self):
        """Login zhihu by mobile"""
        # todo implement login by mobile

    async def login_by_qrcode(self):
        """login zhihu website and keep webdriver login state"""
        utils.logger.info("[ZhiHu.login_by_qrcode] Begin login zhihu by qrcode ...")
        
        # Try multiple selectors for QR code canvas
        qrcode_selectors = [
            "canvas.Qrcode-qrcode",  # Original selector
            "canvas[class*='qrcode']",  # Generic class selector
            "canvas",  # Fallback to any canvas
            ".Qrcode-content canvas",  # Container-based selector
            "[data-testid='qrcode'] canvas"  # Data attribute selector
        ]
        
        base64_qrcode_img = None
        for selector in qrcode_selectors:
            try:
                utils.logger.info(f"[ZhiHu.login_by_qrcode] Trying selector: {selector}")
                base64_qrcode_img = await utils.find_qrcode_img_from_canvas(
                    self.context_page,
                    canvas_selector=selector
                )
                if base64_qrcode_img:
                    utils.logger.info(f"[ZhiHu.login_by_qrcode] Found QR code with selector: {selector}")
                    break
            except Exception as e:
                utils.logger.warning(f"[ZhiHu.login_by_qrcode] Selector {selector} failed: {e}")
                continue
        
        if not base64_qrcode_img:
            utils.logger.error("[ZhiHu.login_by_qrcode] Login failed, could not find QR code with any selector")
            # Try alternative approach - navigate to login page directly
            await self._navigate_to_login_page()
            
            # Retry with selectors after navigation
            for selector in qrcode_selectors:
                try:
                    base64_qrcode_img = await utils.find_qrcode_img_from_canvas(
                        self.context_page,
                        canvas_selector=selector
                    )
                    if base64_qrcode_img:
                        break
                except:
                    continue
            
            if not base64_qrcode_img:
                utils.logger.error("[ZhiHu.login_by_qrcode] All QR code detection methods failed")
                sys.exit()

        # show login qrcode
        # fix issue #12
        # we need to use partial function to call show_qrcode function and run in executor
        # then current asyncio event loop will not be blocked
        partial_show_qrcode = functools.partial(utils.show_qrcode, base64_qrcode_img)
        asyncio.get_running_loop().run_in_executor(executor=None, func=partial_show_qrcode)

        utils.logger.info(f"[ZhiHu.login_by_qrcode] waiting for scan code login, remaining time is 120s")
        try:
            await self.check_login_state()

        except RetryError:
            utils.logger.info("[ZhiHu.login_by_qrcode] Login zhihu failed by qrcode login method ...")
            sys.exit()

        wait_redirect_seconds = 5
        utils.logger.info(
            f"[ZhiHu.login_by_qrcode] Login successful then wait for {wait_redirect_seconds} seconds redirect ...")
        await asyncio.sleep(wait_redirect_seconds)

    async def _navigate_to_login_page(self):
        """Navigate to Zhihu login page directly"""
        utils.logger.info("[ZhiHu._navigate_to_login_page] Navigating to Zhihu login page...")
        
        # Navigate to Zhihu login page
        login_url = "https://www.zhihu.com/signin"
        await self.context_page.goto(login_url, wait_until="networkidle")
        
        # Wait for page to load
        await self.context_page.wait_for_load_state("networkidle")
        
        # Try to click QR code login tab if available
        qr_tab_selectors = [
            "[data-tab='qrcode']",
            ".SignFlow-qrcodeTab",
            "button[aria-label*='二维码']",
            "button:has-text('二维码')"
        ]
        
        for selector in qr_tab_selectors:
            try:
                qr_tab = await self.context_page.query_selector(selector)
                if qr_tab:
                    await qr_tab.click()
                    utils.logger.info(f"[ZhiHu._navigate_to_login_page] Clicked QR code tab with selector: {selector}")
                    await asyncio.sleep(2)  # Wait for QR code to load
                    break
            except Exception as e:
                utils.logger.warning(f"[ZhiHu._navigate_to_login_page] Failed to click QR tab {selector}: {e}")
                continue

    async def login_by_cookies(self):
        """login zhihu website by cookies"""
        utils.logger.info("[ZhiHu.login_by_cookies] Begin login zhihu by cookie ...")
        for key, value in utils.convert_str_cookie_to_dict(self.cookie_str).items():
            await self.browser_context.add_cookies([{
                'name': key,
                'value': value,
                'domain': ".zhihu.com",
                'path': "/"
            }])
