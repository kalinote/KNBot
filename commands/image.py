import requests
from io import BytesIO
import base64
import aiohttp

from amiyabot import Chain, Message
from langchain_community.llms.ollama import Ollama

from commands.command_meta import BaseMeta
from configs import ollama_base_url
from bot import bot

async def fetch_image_as_base64(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # 确保请求成功
            if response.status == 200:
                image_bytes = BytesIO(await response.read())
                image_base64 = base64.b64encode(image_bytes.getvalue()).decode()
                return image_base64
            else:
                print(f"Error fetching image: {response.status}")
                return None

class Meta(BaseMeta):
    command = "[测试功能]图片分析"
    description = "自动识别和分析发送消息中的图片内容，并进行总结。<br />该功能对图片中的英文文字识别有**显著**优势"

async def image_analyze(data: Message):
    for image_url in data.image:
        image_base64 = await fetch_image_as_base64(image_url)

        if not image_base64:
            continue

        # await bot.send_message(Chain().text(image_base64), channel_id=data.channel_id)
        ollama = Ollama(base_url=ollama_base_url, model="llava")
        llm_context = ollama.bind(images=[image_base64])
        result = llm_context.invoke("Describe the content of this image in detail")

        await bot.send_message(Chain().text(str(result)), channel_id=data.channel_id)

    return

image_analyze.Meta = Meta
