import os

from nonebot import on_command
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.red.event import GroupMessageEvent
import requests
import re

voice_file_name = "voice/alice.wav"
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
        with open(voice_file_name, "wb") as file:
            file.write(resp.content)
        return "voice/alice.wav"
    else:
        return ""


def remove_action(line: str) -> str:
    """
    去除括号里描述动作的部分（要求AI输出格式固定）
    :param line:
    :return:
    """
    pattern = r'\（\w+\）'
    match = re.findall(pattern, line)
    if len(match) == 0:
        return line
    else:
        print(f"有{len(match)+1}段描述动作的语句")
        for i in range(len(match)):
            line.replace(match[i], "")
        return line


@speaker.handle()
async def speak(event: GroupMessageEvent):
    line = str(event.message).replace("/说话 ", "")
    await speaker.send(MessageSegment.voice(get_audio(line)))







