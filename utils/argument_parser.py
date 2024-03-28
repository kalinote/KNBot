import argparse
import shlex

from exceptions.throw_message import ThrowMessage


class ArgumentParser(argparse.ArgumentParser):

    def do_parse(self, command):
        # 帮助信息
        parameters = shlex.split(command)[1:]
        if '-h' in parameters or '--help' in parameters:
            raise ThrowMessage(self.format_help())

        # 解析命令
        try:
            args = self.parse_args(args=parameters)
        except Exception as e:
            raise ThrowMessage(f"参数解析错误: {e}\n该命令使用方法如下:\n{self.format_help()}")

        return args

    def error(self, message):
        raise ThrowMessage(message)
