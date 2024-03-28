import json
import re
import warnings
from typing import List, Tuple

import requests
from langchain_core.documents import Document
from langchain_community.document_loaders.base import BaseLoader
from configs import bili_sessdata, bili_bili_jct, bili_buvid3, proxy_ip, proxy_port

class BiliBiliLoader(BaseLoader):
    """Load `BiliBili` video transcripts."""

    def __init__(self, video_urls: List[str]):
        """Initialize with bilibili url.

        Args:
            video_urls: List of bilibili urls.
        """
        self.video_urls = video_urls
        from bilibili_api import settings
        settings.proxy = f"http://{proxy_ip}:{proxy_port}"
        

    async def load(self) -> List[Document]:
        """Load Documents from bilibili url."""
        results = []
        for url in self.video_urls:
            transcript, video_info = await self._get_bilibili_subs_and_info(url)
            doc = Document(page_content=transcript, metadata=video_info)
            results.append(doc)

        return results

    async def _get_bilibili_subs_and_info(self, url: str) -> Tuple[str, dict]:
        try:
            from bilibili_api import video, Credential
        except ImportError:
            raise ImportError(
                "需求包(bilibili-api-python)未找到, 尝试使用以下命令进行安装: "
                "`pip install bilibili-api-python`"
            )

        credential = Credential(
            sessdata=bili_sessdata,
            bili_jct=bili_bili_jct,
            buvid3=bili_buvid3
        )

        bvid = re.search(r"BV\w+", url)
        if bvid is not None:
            v = video.Video(bvid=bvid.group(), credential=credential)
        else:
            aid = re.search(r"av[0-9]+", url)
            if aid is not None:
                try:
                    v = video.Video(aid=int(aid.group()[2:]), credential=credential)
                except AttributeError:
                    raise ValueError(f"{url} is not bilibili url.")
            else:
                raise ValueError(f"{url} is not bilibili url.")

        video_info = await v.get_info()
        video_info.update({"url": url})
        sub = await v.get_subtitle(video_info["cid"])

        # Get subtitle url
        sub_list = sub["subtitles"]
        if sub_list:
            sub_url = sub_list[0]["subtitle_url"]
            if not sub_url.startswith("http"):
                sub_url = "https:" + sub_url
            result = requests.get(sub_url)
            raw_sub_titles = json.loads(result.content)["body"]
            raw_transcript = " ".join([c["content"] for c in raw_sub_titles])

            raw_transcript_with_meta_info = (
                f"Video Title: {video_info['title']},"
                f"description: {video_info['desc']}\n\n"
                f"Transcript: {raw_transcript}"
            )
            return raw_transcript_with_meta_info, video_info
        else:
            raw_transcript = ""
            warnings.warn(
                f"""
                No subtitles found for video: {url}.
                Return Empty transcript.
                """
            )
            return raw_transcript, video_info
