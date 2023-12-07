import os

from nonebot import on_command
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.red.event import GroupMessageEvent
import requests
import time


speaker = on_command("说话 ")


def get_audio(line: str) -> str:
    """
    通过VITS获取语音，返回文件名
    :return:
    """
    print(line)
    _headers = {"Content-Type": "application/json"}
    with requests.session() as sess:
        resp = sess.get(
            f" http://127.0.0.1:23456/voice/vits?text={line}&id=0&format=wav",
            headers=_headers,
            timeout=60,
        )
    if resp.status_code == 200:
        with open("voice/alice.wav", "wb") as file:
            file.write(resp.content)
        return "voice/alice.wav"
    else:
        return ""






