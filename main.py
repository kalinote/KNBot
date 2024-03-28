import re
import asyncio

from amiyabot import Message, Chain

from bot import bot, ChromeBrowserLauncher
from configs import proxy_ip, proxy_port
from commands.command_parser import do_command
from commands import megnet_link, bili_video_summarize

# 匹配磁力链
async def megnet_link_verify(data: Message):
    return "magnet:" in data.text and "xt=urn:btih:" in data.text
@bot.on_message(verify=megnet_link_verify)
async def _(data: Message):
    return await megnet_link(data)

# 匹配BV号(暂时)
async def bv_verify(data: Message):
    pattern = r'BV1.{2}4.{3}7[a-zA-Z0-9]{2,}'
    return bool(re.findall(pattern, data.text))
@bot.on_message(verify=bv_verify)
async def _(data: Message):
    return await bili_video_summarize(data)

# 匹配#开头的指令
async def command_verify(data: Message):
    return True if data.text.startswith("#") else None
@bot.on_message(verify=command_verify)
async def _(data: Message):    
    return await do_command(data)

asyncio.run(bot.start(launch_browser=ChromeBrowserLauncher()))
