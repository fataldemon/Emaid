import re


def remove_emotion(message: str) -> str:
    pattern = r'\【[^\】^\]]*[\]\】]'
    match = re.findall(pattern, message)
    if not len(match) == 0:
        print(match)
        print(f"emotion:{match[0]}")
        return message.replace(match[0], "")
    else:
        return message


def check_emotion(message: str) -> str:
    """
    检查情绪（在对话中以【】格式表示）
    :param message:
    :return:
    """
    pattern = r'\【[^\】^\]]*[\]\】]'
    match = re.findall(pattern, message)
    if not len(match) == 0:
        print(match)
        print(f"emotion:{match[0]}")

        def text_to_emoji(text: str) -> str:
            emojis = {
                "【认真】": "emoji/angry.png",
                "【坚定】": "emoji/angry.png",
                "【生气】": "emoji/angry.png",
                "【诚实】": "emoji/awake.png",
                "【期待】": "emoji/awake.png",
                "【回答】": "emoji/awake.png",
                "【建议】": "emoji/awake.png",
                "【好奇】": "emoji/awake.png",
                "【自信】": "emoji/confident.png",
                "【自豪】": "emoji/confident.png",
                "【委屈】": "emoji/cry.png",
                "【伤心】": "emoji/cry.png",
                "【高兴】": "emoji/happy.png",
                "【开心】": "emoji/happy.png",
                "【愉快】": "emoji/happy.png",
                "【兴奋】": "emoji/happy.png",
                "【快乐】": "emoji/happy.png",
                "【为难】": "emoji/awkward.png",
                "【紧张】": "emoji/awkward.png",
                "【困惑】": "emoji/awkward.png",
                "【困扰】": "emoji/awkward.png",
                "【疑惑】": "emoji/awkward.png",
                "【害怕】": "emoji/sweating.png",
                "【平和】": "emoji/plain.png",
                "【慌张】": "emoji/screwup.png",
                "【害羞】": "emoji/shy.png",
                "【羞涩】": "emoji/shy.png",
                "【微笑】": "emoji/confident.png",
                "【惊喜】": "emoji/smile.png",
                "【理解】": "emoji/smile.png",
                "【流汗】": "emoji/sweating.png",
                "【震惊】": "emoji/sweating.png",
                "【惊讶】": "emoji/sweating.png",
                "【思考】": "emoji/thinking.png",
                "【沉思】": "emoji/thinking.png",
                "【否认】": "emoji/thinking.png",
                "【睡觉】": "emoji/thinking.png",
                "【解释】": "emoji/thinking.png",
                "【感动】": "emoji/touching.png",
                "【感激】": "emoji/touching.png",
                "【道歉】": "emoji/sweating.png",
            }
            if emojis.get(text) is not None:
                return emojis.get(text)
            else:
                return ""

        return text_to_emoji(match[0].replace("]", "】"))
    else:
        return ""
