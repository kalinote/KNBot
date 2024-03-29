import asyncio


from amiyabot import Chain
from amiyabot import Message
from playwright.async_api import async_playwright
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_community.llms.ollama import Ollama

from utils.argument_parser import ArgumentParser
from bot import bot
from configs import proxy_ip, proxy_port, ollama_base_url
from commands.command_meta import BaseMeta

def get_middle_chars(s, n):
    middle = len(s) // 2
    start = middle - n // 2
    end = start + n
    return s[start:end]

def split_string(string, n):
    return [string[i:i+n] for i in range(0, len(string), n)]



class Meta(BaseMeta):
    command = "#搜索"
    description = "通过搜索引擎搜索相关内容, 并通过LLM进行资料整理。"

async def search_website(data: Message):
    # 解析参数
    parser = ArgumentParser(prog=Meta.command, description=Meta.description, exit_on_error=False)

    # 添加选项和参数
    parser.add_argument('-k', '--keyword', type=str, default="kalinote.top", help="需要搜索的关键词，默认为\"kalinote.top\"")
    parser.add_argument('-n', '--number', type=int, default=3, help="总结搜索结果的条数(比如指定为3则总结搜索结果的前3个页面内容)")

    # 解析命令
    try:
        args = parser.do_parse(data.text)
    except Exception as info:
        # 实际上不一定是错误，-h也会触发
        return Chain(data).text(info.__str__())

    keyword = args.keyword
    number = args.number
    url = f"https://www.google.com/search?q={keyword}"

    await bot.send_message(Chain().text("[实验功能]正在请求搜索内容, 请稍等..."), channel_id=data.channel_id)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            proxy={
                "server": f"{proxy_ip}:{proxy_port}",
                "username": "",
                "password": ""
            }
        )
        page = await browser.new_page()
        await page.goto(url, wait_until="load")

        # 处理机器人验证
        if await page.query_selector("#rc-anchor-container"):
            # print("执行了处理机器人验证")
            await page.click("#rc-anchor-container")

        h3_elements = await page.query_selector_all('h3')
        if not h3_elements:
            # 页面中没有h3元素
            await bot.send_message(Chain().text("出现错误, 没有在google的搜索页面找到h3, 请稍后或换一个关键词重试！"), channel_id=data.channel_id)
            # print(await page.content())
            screenshot_bytes = await page.screenshot(full_page=True)
            return Chain(data).image(screenshot_bytes)
        
        links = []
        for h3_element in h3_elements:
            parent_element = await h3_element.query_selector("xpath=..")
            if not parent_element:
                continue
            href = await parent_element.get_attribute('href')
            if href is not None:
                # 找到具有href属性的父元素
                links.append(href)
            
            if len(links) >= number:
                break

        await bot.send_message(Chain().text(f"links: \n{str(links)}"), channel_id=data.channel_id)

        # screenshot_bytes = await page.screenshot(full_page=True)
        # await bot.send_message(Chain().image(screenshot_bytes), channel_id=data.channel_id)

    loader = WebBaseLoader(links)
    docs = loader.load()

    # await bot.send_message(Chain().text(f"原文如下：\n{str(docs)}"), channel_id=data.channel_id)
    
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=20)
    all_splits = text_splitter.split_documents(docs)

    ollama = Ollama(base_url=ollama_base_url, model="qwen:14b")
    chain = load_summarize_chain(ollama, chain_type="map_reduce")
    en_result = chain.run(all_splits)

    await bot.send_message(Chain().text(en_result), channel_id=data.channel_id)

    return

search_website.Meta = Meta
