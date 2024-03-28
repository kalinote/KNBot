import time

from amiyabot import Message, Chain
from utils.argument_parser import ArgumentParser
from utils.authorization import authorization_check
from commands.command_meta import BaseMeta

from bot import bot_name, bot

class Meta(BaseMeta):
    command = "#停止"
    description = f"保存相关运行状态，并关闭{bot_name}"

async def stop_bot(data: Message):
    # 解析参数
    parser = ArgumentParser(prog=Meta.command, description=Meta.description, exit_on_error=False)

    # 解析命令
    try:
        args = parser.do_parse(data.text)
    except Exception as info:
        # 实际上不一定是错误，-h也会触发
        return Chain(data).text(info.__str__())

    if not authorization_check(data.user_id):
        return Chain().at(data.user_id).text(f"你没有权限使用该命令！")
        
    await bot.send_message(Chain().at(data.user_id).text(f"正在保存相关运行状态，并关闭{bot_name}..."), channel_id=data.channel_id)


    # 后续添加一些状态保存相关的代码
    await bot.send_message(Chain().at(data.user_id).text(f"{bot_name}已完成状态保存工作，执行退出程序。"),
                            channel_id=data.channel_id)
    # 需要给点延迟，不然最后一句话发不出去
    time.sleep(3)
    await bot.close()

stop_bot.Meta = Meta
