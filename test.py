from langchain_community.llms.ollama import Ollama
from local_langchain_loaders.bilibili import BiliBiliLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain

from configs import ollama_base_url

ollama = Ollama(base_url=ollama_base_url, model="qwen:7b")
loader = BiliBiliLoader(["https://www.bilibili.com/video/BV1xt411o7Xu/"])
data = loader.load()

text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
all_splits = text_splitter.split_documents(data)

print(len(all_splits))

chain = load_summarize_chain(ollama, chain_type="refine", verbose=True)
en_result = chain.run(all_splits)
print(en_result)
print("\n----------------\n")

ch_result = ollama(f"将这段文本翻译成中文，并且只返回翻译结果: {en_result}")
print(ch_result)
