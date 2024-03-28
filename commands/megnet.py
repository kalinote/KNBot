import os
import re
import time
import json

import aiohttp
from aiohttp import TCPConnector
from aiohttp.client_exceptions import ClientConnectorError
from amiyabot import Chain, Message, log
from commands.command_meta import BaseMeta
from urllib.parse import urlparse, parse_qs

from bot import bot
from configs import bot_host, bot_http_port, token

def _extract_magnet_links(text):
    pattern = r'magnet:\?(?:xt=urn:btih:[\w]{32,40}|[\w]{40})(?:&[\w%.-:+]+=[\w%.-:+]+)*'
    links = re.findall(pattern, text)
    return links

def _get_magnet_hash(magnet_link):
    try:
        parsed_link = urlparse(magnet_link)
        query_components = parse_qs(parsed_link.query)
        hash_value = query_components["xt"][0].split(":")[-1]
        return hash_value
    except Exception as e:
        log.error(f"提取哈希值时出错: {e}")
        return None

import qbittorrentapi
qbt_client = qbittorrentapi.Client(host='127.0.0.1:37890', username='knbot', password='T-o9Up4TEUGcTvAddUGmC-ATugh-VYGv')

class Meta(BaseMeta):
    command = "磁力链接识别"
    description = "自动识别发送消息中的所有megnet磁力链接"

async def megnet_link(data: Message):
    try:
        qbt_client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        return Chain(data).text(f"megnet库认证失败: {e}")

    magnet_links = _extract_magnet_links(data.text)

    downloading_meta = set()
    meta_download_finished = {}
    meta_download_failed = {}

    for magnet_link in magnet_links:
        hash_code = _get_magnet_hash(magnet_link)
        await bot.send_message(Chain().text(f"[实验功能]检测到磁力hash: {hash_code}"), channel_id=data.channel_id)
        downloading_meta.add(hash_code)
        result = qbt_client.torrents_add(urls=magnet_link, stop_condition="MetadataReceived")

    start_time = time.time()

    while True:
        if time.time() - start_time > 30:  # 检查是否已超过30秒
            for hash in downloading_meta:
                meta_download_failed[hash] = "种子文件下载超时"
            break
        
        time.sleep(1)
        for hash in downloading_meta.copy():
            info = qbt_client.torrents_info(torrent_hashes=hash)[0]

            if info.state != "metaDL":
                downloading_meta.remove(hash)
                meta_download_finished[hash] = info

        if not downloading_meta:
            break

    for hash in meta_download_finished.keys():
        files = qbt_client.torrents_files(torrent_hash=hash)

        await bot.send_message(Chain().text(f"{hash[:6]} 种子包含 {files[0].name} 等 {len(files)} 个文件"), channel_id=data.channel_id)

        all_file = {
            "report_time": time.time(),
            "torrent_hash": hash,
            "torrent_name": meta_download_finished[hash].get("name"),
            "magnet_uri": meta_download_finished[hash].get("magnet_uri"),
            "total_size": meta_download_finished[hash].get("total_size"),
            "tracker": meta_download_finished[hash].get("tracker"),
            "total_files": len(files),
            "file_list": []
        }
        for file in files:
            all_file["file_list"].append({
                "index": file.index,
                "name": file.name,
                "priority": file.priority,
                "size": file.size,
                "id": file.id
            })

        with open(f"./temp_files/[磁力链接报告]{hash}.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(all_file, ensure_ascii=False, indent=4))

        async with aiohttp.ClientSession(connector=TCPConnector(ssl=False)) as session:
            try:
                async with aiohttp.ClientSession() as session:
                    response = await session.post(
                        url=f"http://{bot_host}:{bot_http_port}/send_group_msg?access_token={token}",
                        json={
                            "group_id": str(data.channel_id),
                            "message": {
                                "type": "file",
                                "data": {
                                    "file": f"file:///{os.path.abspath(f'./temp_files/[磁力链接报告]{hash}.json')}",
                                    "name": f"[磁力链接报告]{hash}.json"
                                }
                            }
                        }
                    )

                # 确保响应状态码为200
                if response.status == 200:
                    # 使用await调用response.json()以异步获取JSON数据
                    json_data = await response.json()
                    if not json_data.get("status") == "ok":
                        return f"上传文件请求失败，返回数据：\n{json.dumps(json_data, ensure_ascii=False, indent=4)}"
                else:
                    return f"上传文件请求失败，状态码：{response.status}"

            except Exception as e:
                log.error(f"在上传文件时发生了错误: {e}({type(e)})")
                return f"在上传文件时发生了错误: {e}"

    return Chain(data).text(f"全部处理完毕" + (f", 其中 {', '.join([h[:6] for h in meta_download_failed.keys()])} 因元数据解析超时下载失败" if len(meta_download_failed) > 0 else ""))

megnet_link.Meta = Meta
