import re

from langchain_community.llms.ollama import Ollama
from local_langchain_loaders.bilibili import BiliBiliLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from amiyabot import Chain, Message, log

from commands.command_meta import BaseMeta
from configs import ollama_base_url
from bot import bot

def extract_bv(input_string):
    pattern = r'BV1.{2}4.{3}7[a-zA-Z0-9]{2,}'
    matches = re.findall(pattern, input_string)
    valid_strings = [match[:12] for match in matches]
    return valid_strings

class Meta(BaseMeta):
    command = "[测试功能]B站视频总结"
    description = "自动识别发送消息中的BV号(暂时)，并总结视频内容"

async def bili_video_summarize(data: Message):
    bvids = extract_bv(data.text)
    if not bvids:
        return
    await bot.send_message(Chain().text(f"[实验功能]监测到BV号: {', '.join(bvids)}"), channel_id=data.channel_id)

    ollama = Ollama(base_url=ollama_base_url, model="qwen:14b")

    for bv in bvids:
        loader = BiliBiliLoader([f"https://www.bilibili.com/video/{bv}/"])
        v_data = await loader.load()

        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
        all_splits = text_splitter.split_documents(v_data)

        chain = load_summarize_chain(ollama, chain_type="refine")
        en_result = chain.run(all_splits)

        await bot.send_message(Chain().text(f"[测试] {bv} 总结原文: \n{en_result}"), channel_id=data.channel_id)

    return

bili_video_summarize.Meta = Meta
