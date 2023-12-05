from nonebot import on_command
from nonebot import on_message
from nonebot.adapters.red.event import GroupMessageEvent
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.qq import Message, MessageEvent
from nonebot.params import CommandArg


def _checker(event: GroupMessageEvent) -> bool:
    return event.to_me


a = on_command("测试", rule=_checker)


@a.handle()
async def _(event: GroupMessageEvent):
    await a.send(f"{event.message}")
