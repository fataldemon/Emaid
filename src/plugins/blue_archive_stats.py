import json
import os

from nonebot import on_command
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.red.event import GroupMessageEvent
import requests

ba_stats = on_command("攻略 ")


def get_png(hash_code: str, url: str) -> str:
    if os.path.exists(f"ba_stats/{hash_code}.png"):
        print("图片已缓存，无需下载")
        return f"ba_stats/{hash_code}.png"
    else:
        def download_image(_url, file_name):
            response = requests.get(_url)
            with open(file_name, "wb") as file:
                file.write(response.content)

        download_image(url, f"ba_stats/{hash_code}.png")
        print("图片下载完成")
        return f"ba_stats/{hash_code}.png"


@ba_stats.handle()
async def ba_search(event: GroupMessageEvent):
    """
    获取碧蓝档案攻略
    :param event:
    :return:
    """
    info = str(event.message).replace("/攻略 ", "")
    _headers = {"Content-Type": "application/json"}
    with requests.session() as sess:
        resp = sess.get(
            f"https://arona.diyigemt.com/api/v2/image?name={info}",
            headers=_headers,
            timeout=60,
        )
    if resp.status_code == 200:
        resp_json = json.loads(resp.text)
        data = resp_json["data"]
        if len(data) == 1:
            await ba_stats.send(MessageSegment.image(get_png(data[0]["hash"], "https://arona.cdn.diyigemt.com/image/s"+data[0]["content"])))
        else:
            tips = ""
            for i in range(len(data)):
                tips += data[i]["name"]+" "
            tips += "\n爱丽丝找到了这些信息条目，请按照条目继续查询！"
            await ba_stats.send(tips)


