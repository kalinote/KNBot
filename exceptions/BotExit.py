# 这个原本用于处理bot退出，但是后面更改了处理方法，现在暂时没用了
from configs import bot_name


class BotExit(Exception):
    def __init__(self, data, message=f'执行{bot_name}退出处理程序'):
        self.data = data
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"管理员于群{self.data.channel_id}中{self.message}"
