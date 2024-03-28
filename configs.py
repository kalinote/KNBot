# configs.py
import yaml

def load_configs():
    with open('configs.yaml', 'r', encoding='utf-8') as file:
        configs = yaml.safe_load(file)
        globals().update(configs)

load_configs()
