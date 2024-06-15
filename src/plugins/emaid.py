import datetime

import nonebot
from nonebot import on_message
from nonebot import on_command
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.red.event import MessageEvent, GroupMessageEvent
from src.plugins.chatglmOpenapi import ChatGLM
from src.plugins.qwenOpenapi import Qwen
from src.plugins.emotion import remove_emotion, check_emotion
from src.plugins.voice import get_audio, remove_action, get_translation, voice_generate
from src.plugins.embedding import vector_search
from src.skills.game_status_process import set_field,  get_master_id, clear_death_list, get_game_status, donate, get_ban_words

# 管理员身份
master_id = get_master_id()

# 语音开关
GROUP_SWITCH: bool = False
AUDIO_SWITCH: bool = False
TRANSLATE_SWITCH: bool = True
user_blacklist = []
username_blacklist = []
message_buffer = {}

# 对话者名字记忆区
talker_list = {
}

# 调用工具定义
tools_list = [
            {
                'name_for_human': '光之剑',
                'name_for_model': 'sword_of_light',
                'description_for_model': '光之剑是爱丽丝的武器，可以用光之剑发射电磁炮攻击敌人，当遭遇敌人时使用。',
                'parameters': [
                    {
                        'name': 'target',
                        'description': '攻击目标的名字',
                        'required': True,
                        'schema': {'type': 'string'},
                    }
                ],
            },
            {
                'name_for_human': '移动到其他地点',
                'name_for_model': 'move',
                'description_for_model': '离开当前场景，去往其他地点。',
                'parameters': [
                    {
                        'name': 'to',
                        'description': '接下来要前往的场景或地点的名称',
                        'required': False,
                        'schema': {'type': 'string'},
                    }
                ],
            },
            {
                'name_for_human': '道具搜索',
                'name_for_model': 'search_for_item',
                'description_for_model': '在当前场景下展开搜索，寻找可以拾取的隐藏道具，就像RPG游戏的主角一样',
                'parameters': [
                    {
                        'name': 'object',
                        'description': '指定具体的搜索对象，例如宝箱、房屋、垃圾箱等',
                        'required': False,
                        'schema': {'type': 'string'},
                    }
                ],
            },
            {
                'name_for_human': '联网查找信息',
                'name_for_model': 'search_on_internet',
                'description_for_model': '在互联网上搜索、查找相关信息',
                'parameters': [
                    {
                        'name': 'query',
                        'description': '需要查找信息的条目',
                        'required': True,
                        'schema': {'type': 'string'},
                    }
                ],
            },
      ]

tools = [tools_list[0], tools_list[1], tools_list[3]]

# 调用大模型对象列表（记忆体按照群号区分）
llm_list: dict = {}


def getLLM(group_id: str) -> ChatGLM:
    """
    按照群号获取大语言模型（为了分别存储记忆）
    :return:
    """
    if llm_list.get(group_id) is None:
        # llm = ChatGLM(history=history6, temperature=0.6, top_p=0.5, repetition_penalty=1.2)
        # llm = Qwen(temperature=0.95, top_p=0.7, functions=tools, repetition_penalty=1.10, max_history=12)
        llm = Qwen(temperature=0.95, top_p=0.4, functions=tools, repetition_penalty=1.10, max_history=12)
        llm_list[group_id] = llm
        return llm
    else:
        return llm_list.get(group_id)


def _master_checker(event: GroupMessageEvent) -> bool:
    user_id = event.senderUin
    print(user_id)
    if user_id in master_id:
        return True
    else:
        return False


def _checker(event: GroupMessageEvent) -> bool:
    """
    检查是否触发（通过@），但过滤通过/发起的命令
    :param event:
    :return:
    """
    user_id = event.senderUin
    if user_id in user_blacklist:
        return False
    message = str(event.message)
    if message.startswith("/") and not message.startswith("/记忆清除术") and not message.startswith("/给你钱") and not message.startswith("/momotalk"):
        return False
    else:
        return event.to_me


def _none_checker(event: GroupMessageEvent) -> bool:
    """
    检查是否触发（通过@），但过滤通过/发起的命令
    :param event:
    :return:
    """
    user_id = event.senderUin
    if user_id in user_blacklist:
        return False
    return not event.to_me


def _blacklist_checker(event: GroupMessageEvent) -> bool:
    user_id = event.senderUin
    if user_id in user_blacklist:
        return False
    else:
        return True


assistant = on_command("助手 ")
group_chatter = on_message(rule=_checker, priority=2, block=False)
clear_memory = on_command("记忆清除术", rule=_checker, priority=3)
voice_switch = on_command("语音开关")
black_list = on_command("blacklist ")
unblack_list = on_command("unblacklist ")
set_scene = on_command("goto")
clear_death_zone = on_command("重置墓地")
donation = on_command("给你钱", rule=_checker, priority=1, block=False)
# group_message = on_message(rule=_none_checker, priority=1, block=False)


async def send_chat(prompt: str, group_id: str, embedding, status: str) -> tuple:
    """
    通过接口向LLM发送聊天
    :param embedding: 附加知识内容
    :param group_id: 群组ID
    :param prompt:用户发送的聊天内容
    :return:LLM返回的聊天内容
    """
    llm = getLLM(group_id)
    thought, response, feedback, finish_reason = await llm.call_with_function(prompt, stop=None, embedding=embedding, status=status)
    return thought, response, feedback, finish_reason


async def send_to_assistant(prompt: str, group_id: str) -> tuple:
    """
    通过接口向LLM（不加Lora）发送聊天
    :param group_id: 群组ID
    :param prompt:用户发送的聊天内容
    :return:LLM返回的聊天内容
    """
    llm = getLLM(group_id)
    result = await llm.call_assistant(prompt, stop=None)
    return result


async def send_feedback(feedback: str, group_id: str) -> tuple:
    """
    通过接口向LLM发送API返回结果
    :param group_id: 群组ID
    :param feedback: 函数调用反馈信息
    :param prompt:用户发送的聊天内容
    :return:LLM返回的聊天内容
    """
    llm = getLLM(group_id)
    thought, response, feedback, finish_reason = await llm.send_feedback(feedback, stop=None)
    return thought, response, feedback, finish_reason


# 通过QQ号获取对话者名字（未记录的按照同学A、B、C、D）
def get_talker_name(user_id: str) -> str:
    global talker_list
    print(f"对话者总数：{len(talker_list)}")
    if talker_list.get(user_id) is not None:
        return talker_list.get(user_id)
    else:
        talker_list[user_id] = f"{chr(len(talker_list)+65)}"
        return talker_list.get(user_id)


def user_name_filter(user_id: str, user_name: str) -> str:
    # 过滤屏蔽词
    user_name = user_name.replace("中国", "")
    user_name = user_name.replace("的", "")
    user_name = remove_action(user_name)
    if user_name == "" or len(user_name) >= 8:
        return get_talker_name(user_id)
    else:
        return user_name


def sword_of_light(user_name: str):
    """
    光之剑！将一名敌人送入墓地（屏蔽操作）
    :param user_name:
    :return:
    """
    username_blacklist.append(user_name)


@voice_switch.handle()
async def turn_switch(event: GroupMessageEvent):
    global AUDIO_SWITCH
    user_id = event.senderUin
    if user_id in master_id:
        if AUDIO_SWITCH:
            AUDIO_SWITCH = False
            await voice_switch.send("语音关闭")
        else:
            AUDIO_SWITCH = True
            await voice_switch.send("语音启动")
    else:
        await voice_switch.send("权限不足")


# @group_message.handle()
# async def save_message_buffer(event: GroupMessageEvent):
#     group_id = event.group_id
#     message = str(event.message)
#     user_id = event.senderUin
#     username = event.sendMemberName
#     if event.sendMemberName == "":
#         username = f"编号为{user_id}的同学"
#     if user_id in master_id:
#         username = "老师"
#     user_name = user_name_filter(user_id, username)
#     if user_name != "老师":
#         user_name += "同学"
#     if message_buffer.get(group_id) is None:
#         message_buffer[group_id] = [f"（{user_name}说）{message}"]
#     else:
#         message_buffer[group_id].append(f"（{user_name}说）{message}")
#         if len(message_buffer[group_id]) > 6:
#             message_buffer[group_id] = message_buffer[group_id][-6:]


@group_chatter.handle()
async def chat(event: GroupMessageEvent):
    message = str(event.message)
    # 获取呼叫用户名
    user_id = event.senderUin
    print("userid="+user_id)
    # 获取群组ID
    group_id = event.group_id
    # 群聊模式
    pre_messages = ""
    if GROUP_SWITCH and message_buffer.get(group_id) is not None:
        for pre_message in message_buffer.get(group_id):
            pre_messages += pre_message + "\n"
        message_buffer[group_id] = []
    # 过滤括号里的内容
    if user_id not in master_id:
        message = remove_action(message)
    knowledge = vector_search(message, 3)

    game_status = get_game_status()
    field = game_status["field"]
    coins = game_status["coins"]
    items = game_status["items"]
    profession_choice = game_status["profession_choice"]
    profession = game_status["job"][profession_choice]["name"]
    level = game_status["job"][profession_choice]["level"]
    experience = game_status["job"][profession_choice]["experience"]
    attack = game_status["job"][profession_choice]["attack"]
    hp = game_status["health"]
    ng_words = get_ban_words()
    status = f"\n当前场景：{field}。" \
             f"\n爱丽丝的状态栏：职业：{profession}；经验值：{experience}/{level*100}；生命值：{hp}；攻击力：{attack}；" \
             f"持有的财富：{coins}点信用积分；装备：“光之剑”（电磁炮）；持有的道具：{items}。"

    username = event.sendMemberName
    if event.sendMemberName == "":
        username = f"编号为{user_id}的同学"
    if user_id in master_id:
        username = "老师"
    print(f"user_id={user_id}, user_name={username}, talker_name={get_talker_name(user_id)}, "
          f"getuserID={event.get_user_id()}")

    current_time = datetime.datetime.now()
    current_date_str = current_time.strftime("今天是%Y年%m月%d日")
    hour = current_time.hour
    if 0 <= hour < 5:
        time_period = "凌晨"
    elif 5 <= hour < 9:
        time_period = "早上"
    elif 9 <= hour < 12:
        time_period = "上午"
    elif 12 <= hour < 14:
        time_period = "中午"
        hour = hour-12
    elif 14 <= hour < 17:
        time_period = "下午"
        hour = hour-12
    elif 17 <= hour < 19:
        time_period = "傍晚"
        hour = hour-12
    elif 19 <= hour < 24:
        time_period = "晚上"
        hour = hour - 12
    current_time_str = current_time.strftime(f"当前时间：{time_period}%H点%M分%S秒。")
    if current_time.weekday() == 0:
        weekday = "一"
    elif current_time.weekday() == 1:
        weekday = "二"
    elif current_time.weekday() == 2:
        weekday = "三"
    elif current_time.weekday() == 3:
        weekday = "四"
    elif current_time.weekday() == 4:
        weekday = "五"
    elif current_time.weekday() == 5:
        weekday = "六"
    else:
        weekday = "日"
    dater = f"{current_date_str}，星期{weekday}，{current_time_str}"
    status = status + "\n" + dater

    tips = "\n（提示："
    if user_id in master_id:
        # 命令提示
        if "使用光之剑" in message or "开火" in message or "发射" in message or "干掉" in message:
            tips += "如果要发射光之剑，请使用sword_of_light的API。）"
        elif "走吧" in message or "出发" in message or "回来" in message or "回到" in message:
            tips += "如果要离开当前地点，请使用move的API。）"
        elif "联网查" in message or "上网查" in message or "帮我查" in message or "查一下" in message:
            tips += "如果要上网查询信息，请使用search_on_internet的API。）"
        else:
            tips += "）"

        if message.strip() != "":
            # 打赏
            if message.startswith("/给你钱"):
                message = message.replace("/给你钱", "")
                thought, response, feedback, finish_reason = await send_chat(
                    f"{pre_messages}（{username}给了爱丽丝1信用点，爱丽丝的财富增加了。目前爱丽丝有{coins}点信用积分。）" + message,
                    group_id, knowledge, status)
            # Momotalk
            elif message.startswith("/momotalk"):
                message = message.replace("/momotalk", "")
                if message.strip() == "":  # 收到爱丽丝信息
                    thought, response, feedback, finish_reason = await send_chat(
                        f"{pre_messages}（{username}收到了从爱丽丝那里发来的Momotalk信息）",
                        group_id, knowledge, status)
                else:  # 给爱丽丝发送信息
                    thought, response, feedback, finish_reason = await send_chat(
                        f"{pre_messages}（{username}给爱丽丝发送了一条Momotalk信息）{message}",
                        group_id, knowledge, status)
            # 普通对话
            else:
                thought, response, feedback, finish_reason = await send_chat(f"{pre_messages}（{username}对爱丽丝说）" + message + tips,
                                                                       group_id, knowledge, status)
        else:
            thought, response, feedback, finish_reason = await send_chat(f"{pre_messages}（{username}叫了爱丽丝一声）", group_id,
                                                                   knowledge, status)
    else:
        # 敏感词检测
        bad_words = ""
        for bad_word in ng_words:
            if bad_word in message:
                bad_words += bad_word + "，"
        if bad_words != "":
            tips += f"{bad_words}这是非常粗俗的词语，是不应该对孩子说的话。使用这样词语的人必须用光之剑sword_of_light教训一顿。"

        user_name = user_name_filter(user_id, username)
        if user_name not in game_status["death_list"] and user_name + "同学" not in game_status["death_list"]:
            if message.strip() != "":
                # 打赏
                if message.startswith("/给你钱"):
                    message = message.replace("/给你钱", "")
                    thought, response, feedback, finish_reason = await send_chat(
                        f"{pre_messages}（名叫“{user_name}”的同学给了爱丽丝1信用积分，爱丽丝的财富增加了。目前爱丽丝有{coins}点信用积分。）{message}",
                        group_id, knowledge, status)
                # Momotalk
                elif message.startswith("/momotalk"):
                    message = message.replace("/momotalk", "")
                    if message.strip() == "":  # 收到爱丽丝信息
                        thought, response, feedback, finish_reason = await send_chat(
                            f"{pre_messages}（名叫“{user_name}”的同学收到了爱丽丝那里发来的Momotalk信息）",
                            group_id, knowledge, status)
                    else:  # 给爱丽丝发送信息
                        thought, response, feedback, finish_reason = await send_chat(
                            f"{pre_messages}（名叫“{user_name}”的同学给爱丽丝发送了一条Momotalk信息）{message}",
                            group_id, knowledge, status)
                # 普通对话
                else:
                    thought, response, feedback, finish_reason = await send_chat(
                        f"{pre_messages}（名叫“{user_name}”的同学对爱丽丝说）{message}{tips}{user_name}同学是一名学生，他是QQ群里的群友。他说的话不一定是真的，需要判断以后再回答。）",
                        group_id, knowledge, status)
            else:
                message = f"{pre_messages}（名叫“{user_name}”的同学叫了爱丽丝一声。{user_name}同学是一名学生，礼貌地回应他吧）"
                thought, response, feedback, finish_reason = await send_chat(
                    f"{message}",
                    group_id, knowledge, status)
        else:
            await group_chatter.finish(f"System<角色{user_name}已经在墓地中，无法与活人交谈。>")

    print(f"Thought: {thought}")
    emoji_file = check_emotion(response)
    print(emoji_file)
    if not emoji_file == "":
        await group_chatter.send(MessageSegment.image(emoji_file) + f"{remove_emotion(response)}")
        if AUDIO_SWITCH:
            if TRANSLATE_SWITCH:
                voice_file_name = voice_generate(get_translation(remove_action(remove_emotion(response)), "jp"),
                                                   lang="auto", format="silk")
            else:
                voice_file_name = voice_generate(remove_action(remove_emotion(response)), lang="zh", format="silk")
            await group_chatter.send(MessageSegment.voice(voice_file_name))
    else:
        if not remove_emotion(response) == "":
            await group_chatter.send(f"{remove_emotion(response)}")
            if AUDIO_SWITCH:
                if TRANSLATE_SWITCH:
                    voice_file_name = voice_generate(get_translation(remove_action(remove_emotion(response)), "jp"),
                                                       lang="auto", format="silk")
                else:
                    voice_file_name = voice_generate(remove_action(remove_emotion(response)), lang="zh", format="silk")
                await group_chatter.send(MessageSegment.voice(voice_file_name))
        else:
            await group_chatter.send("...")
    if feedback != "":
        if "（爱丽丝在网络上对〖" in feedback and "〗词条进行了一番搜索，得到了一些信息）" in feedback:
            locator_left = feedback.rfind("〖")
            locator_right = feedback.rfind("〗")
            subject = feedback[locator_left+1:locator_right]
            web_summary = await send_to_assistant(feedback+f"\n\n在150字以内总结上面关于\"{subject}\"的搜索结果：", group_id)
            feedback = f"（爱丽丝在网络上对\"{subject}\"进行了一番搜索，得到了下面的信息）{web_summary}"
        await group_chatter.send(f"System<{feedback}>")
    while finish_reason == "function_call":
        thought, response, feedback, finish_reason = await send_feedback(feedback, group_id)
        print(f"Thought: {thought}")
        emoji_file = check_emotion(response)
        print(emoji_file)
        if not emoji_file == "":
            await group_chatter.send(MessageSegment.image(emoji_file) + f"{remove_emotion(response)}")
            if AUDIO_SWITCH:
                if TRANSLATE_SWITCH:
                    voice_file_name = voice_generate(get_translation(remove_action(remove_emotion(response)), "jp"),
                                                       lang="auto", format="silk")
                else:
                    voice_file_name = voice_generate(remove_action(remove_emotion(response)), lang="zh", format="silk")
                await group_chatter.send(MessageSegment.voice(voice_file_name))
        else:
            if not remove_emotion(response) == "":
                await group_chatter.send(f"{remove_emotion(response)}")
                if AUDIO_SWITCH:
                    if TRANSLATE_SWITCH:
                        voice_file_name = voice_generate(get_translation(remove_action(remove_emotion(response)), "jp"),
                                                           lang="auto", format="silk")
                    else:
                        voice_file_name = voice_generate(remove_action(remove_emotion(response)), lang="zh", format="silk")
                    await group_chatter.send(MessageSegment.voice(voice_file_name))
            else:
                await group_chatter.send("...")
        if feedback != "":
            await group_chatter.send(f"System<{feedback}>")


@clear_memory.handle()
async def clear_memory_func(event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.senderUin
    if user_id in master_id:
        if message_buffer.get(group_id) is not None:
            message_buffer[group_id] = []
        llm = getLLM(group_id)
        llm.clear_memory()
        await clear_memory.send(f"爱丽丝什么都不记得了！")
    else:
        await clear_memory.send("权限不足")


@black_list.handle()
async def add_black_list(event: GroupMessageEvent):
    user_id = event.senderUin
    if user_id in master_id:
        blacklist_user_id = str(event.message).replace("/blacklist ", "")
        if blacklist_user_id != "":
            user_blacklist.append(blacklist_user_id)
            await black_list.send("黑名单已添加")
        else:
            await black_list.send("QQ号为空")
    else:
        await black_list.send("权限不足")


@unblack_list.handle()
async def remove_black_list(event: GroupMessageEvent):
    user_id = event.senderUin
    if user_id in master_id:
        blacklist_user_id = str(event.message).replace("/unblacklist ", "")
        if blacklist_user_id != "":
            user_blacklist.remove(blacklist_user_id)
            await unblack_list.send("黑名单已清除")
        else:
            await unblack_list.send("QQ号为空")
    else:
        await unblack_list.send("权限不足")


@set_scene.handle()
async def set_scene_manual(event: GroupMessageEvent):
    user_id = event.senderUin
    if user_id in master_id:
        scene = str(event.message).replace("/goto", "")
        if scene.strip() == "":
            scene = "沙勒，老师的办公室"
        set_field(scene)
        await set_scene.send(f"System<爱丽丝所处的场景已设定为“{scene}”>")
    else:
        await set_scene.send("权限不足")


@clear_death_zone.handle()
async def reset_tomb(event: GroupMessageEvent):
    user_id = event.senderUin
    if user_id in master_id:
        clear_death_list()
        await clear_death_zone.send(f"System<当前墓地已经被清空>")
    else:
        await clear_death_zone.send("权限不足")


@donation.handle()
async def donate_money(event: GroupMessageEvent):
    await donation.send(f"System<（爱丽丝得到了1信用点，现在有{donate(1)}信用点）>")


@assistant.handle()
async def assistant_reply(event: GroupMessageEvent):
    group_id = event.group_id
    content = str(event.message).replace("/助手 ", "")
    reply = await send_to_assistant(content, group_id)
    await assistant.send(reply)
