from amiyabot import Message, Chain

from bot import bot_name
from utils.argument_parser import ArgumentParser
from commands import commands
from commands.command_meta import BaseMeta

class Meta(BaseMeta):
    command = "#使用说明"
    description = f"{bot_name} 的使用方法说明"

async def command_help(data: Message):
    # 解析参数
    parser = ArgumentParser(prog=Meta.command, description=Meta.description, exit_on_error=False)

    # 解析命令
    try:
        args = parser.do_parse(data.text)
    except Exception as info:
        # 实际上不一定是错误，-h也会触发
        return Chain(data).text(info.__str__())

    # 生成文档
    help_doc = "# {bot_name} 使用说明\n\n".format(bot_name=bot_name)
    help_doc += f"## {Meta.command}\n{Meta.description}(本页面)\n\n"
    for command in commands:
        help_doc += f"## {command.Meta.command}\n{command.Meta.description}\n\n"
    help_doc += "---\n想要阅读更详细的帮助文档，使用以下命令来获取对应功能的详细文档(包括本命令):\n```shell\n#命令 -h/--help\n```\n"

    return Chain(data).markdown(content=help_doc)

help.Meta = Meta
command_dict = {
    "#使用说明": command_help
}
for command in commands:
    command_dict[command.Meta.command] = command

async def do_command(data: Message):
    """命令解析程序

    Args:
        data (Message): 接受到的数据

    Returns:
        _type_: 需要发送的数据或其他需要返回的数据
    """
    command = data.text.strip().split(" ")[0]
    if command not in command_dict:
        return Chain(data).text(f"无法识别的指令: {command}\n\n使用 #使用说明 查看所有可用指令")

    return await command_dict[command](data)
