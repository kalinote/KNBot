from configs import bot_name, qq, token

from amiyabot.adapters.onebot.v11 import onebot11
from amiyabot import AmiyaBot
from playwright.async_api import Playwright, Browser
from amiyabot import BrowserLaunchConfig

from amiyabot.adapters.test import test_instance

from configs import proxy_ip, proxy_port, bot_host, bot_ws_port, bot_http_port

class ChromeBrowserLauncher(BrowserLaunchConfig):
    def __init__(self):
        super().__init__()

    # 继承并改写 launch_browser 方法
    async def launch_browser(self, playwright: Playwright) -> Browser:
        # 返回通过任意方式创建的 Browser 对象
        return await playwright.chromium.launch(
            proxy={
                "server": f"{proxy_ip}:{proxy_port}",
                "username": "",
                "password": ""
            }
        )


adapter_service = onebot11(host=bot_host, ws_port=bot_ws_port, http_port=bot_http_port)
bot = AmiyaBot(appid=qq, token=token, adapter=adapter_service)
# bot = AmiyaBot(appid=qq, token=token, adapter=test_instance('127.0.0.1', 32001))
