# -*- encoding: utf-8 -*-
import aiohttp
from io import BytesIO
from PIL import Image

class Networks:
    def __init__(self) -> None:
        self.HeadImg = []
        self.EmojiImg = []
        
    async def fetch(self,session, url):
        """实现GET请求"""
        async with session.get(url) as response:
            return await response.read()

    async def getPage(self, url, count=0, tp=0, sz=0):
        """下载图片"""
        async with aiohttp.ClientSession() as session:
            data = await self.fetch(session, url)
            pic = Image.open(BytesIO(data))
            if tp == 0:
                return pic
            elif tp == 1:
                self.HeadImg.append({"data": pic, "path": count, "type": sz})
            else:
                self.EmojiImg.append({"data": pic, "path": count, "id": sz})
            return pic