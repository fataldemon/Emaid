import src.skills.game_status_process as game
from src.skills.online_search import online_search_func
import asyncio


async def skill_call(action: str, action_input: dict) -> str:
    if action == "sword_of_light":
        target = action_input.get("target")
        if target is not None:
            result = hikari_yo(target)
        else:
            result = "光之剑必须指定一个目标！"
    elif action == "move":
        to = action_input.get("to")
        if to is not None:
            result = move(to)
        else:
            result = move("")
    elif action == "search_for_item":
        result = search_for_item()
    elif action == "search_on_internet":
        query = action_input.get("query")
        if query is not None:
            result = await search_on_internet(query)
        else:
            result = "查询参数不能为空！"
    else:
        result = f"技能{action}不存在！"
    return str(result)


def hikari_yo(target: str) -> str:
    game.add_death_list(target)
    return f"（“光之剑”发射出耀眼的光芒，{target}受到了100点伤害，{target}被打倒了。）"


def move(to: str) -> str:
    if to != "":
        game.set_field(to)
        return f"（爱丽丝现在来到了“{to}”场景。）"
    else:
        game.set_field("千禧年校园")
        return f"（爱丽丝现在来到了“千禧年校园”场景。）"


def search_for_item() -> str:
    return f"（爱丽丝花费时间进行了一番搜索，但是一无所获。或许这里应该暂且放弃。）"


async def search_on_internet(item: str) -> str:
    raw_info = await online_search_func(item)
    info = f"（爱丽丝在网络上对〖{item}〗词条进行了一番搜索，得到了一些信息）{raw_info}"
    print(raw_info)
    return info


if __name__ == "__main__":
    result = asyncio.run(skill_call("search_on_internet", {"query": "科比"}))
    print(result)
