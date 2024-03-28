import asyncio

from amiyabot import Chain
from amiyabot import Message
from playwright.async_api import async_playwright

from utils.argument_parser import ArgumentParser
from bot import bot
from configs import proxy_ip, proxy_port, system_order
from commands.command_meta import BaseMeta
from llm.ollama import ollama_client

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

    # 解析命令
    try:
        args = parser.do_parse(data.text)
    except Exception as info:
        # 实际上不一定是错误，-h也会触发
        return Chain(data).text(info.__str__())

    keyword = args.keyword
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
        
        for h3_element in h3_elements:
            parent_element = await h3_element.query_selector("xpath=..")
            if not parent_element:
                continue
            href = await parent_element.get_attribute('href')
            if href is not None:
                # 找到具有href属性的父元素
                await page.goto(href)
                break

        screenshot_bytes = await page.screenshot(full_page=True)
        await bot.send_message(Chain().image(screenshot_bytes), channel_id=data.channel_id)

        elements = await page.query_selector_all("h1, h2, h3, h4, h5, h6, p")
        texts = [await element.inner_text() for element in elements]
        full_content = " ".join(texts)

        # await bot.send_message(Chain().text(f"原文如下：\n{full_content}"), channel_id=data.channel_id)

    content_list = split_string(full_content, 3800)
    count = 0
    for content in content_list:
        count += 1
        results = ollama_client.generate(model='qwen:7b', prompt=f"下面这些文本是从某个网页中提取到的，其中包含了很多杂乱的无用的信息，你需要帮我提取出**所有**有用的信息，不要进行总结，只需要提取出原文，然后进行尽可能详细地解释说明：\n\n{content}",
            options={
                "num_ctx": 4096
            },
            stream=True
        )

        sentence:str = ""
        for chunk in results:
            sentence += chunk["response"]
            print(chunk["response"], end="", flush=True)
            if sentence.endswith("\n\n"):
                await bot.send_message(Chain().text(sentence.rstrip("\n")), channel_id=data.channel_id)
                sentence:str = ""
                await asyncio.sleep(2)

        if sentence:
            await bot.send_message(Chain().text(sentence.rstrip("\n")), channel_id=data.channel_id)

    return

search_website.Meta = Meta
