from ollama import Client
from configs import ollama_base_url

ollama_client = Client(host=ollama_base_url)
