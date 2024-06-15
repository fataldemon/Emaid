import os

from nonebot import on_command
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.red.event import GroupMessageEvent
import requests
import re
import hashlib
import json
import random
from requests_toolbelt.multipart.encoder import MultipartEncoder
from src.plugins.gradio_call import get_audio_from_gradio
import string

voice_file_name = "voice/alice.silk"
speaker = on_command("说话 ")
translator = on_command("翻译 ")
test_amr = on_command("amrtest")

lang_codes = {
    "中文": "zh",
    "简体中文": "zh",
    "汉语": "zh",
    "繁体中文": "cht",
    "文言文": "wyw",
    "英语": "en",
    "英文": "en",
    "日语": "jp",
    "日文": "jp",
    "俄语": "ru",
    "俄文": "ru",
    "法语": "fra",
    "法文": "fra",
    "德语": "de",
    "德文": "de",
    "葡萄牙语": "pt",
    "葡萄牙文": "pt",
    "西班牙语": "spa",
    "西班牙文": "spa",
    "意大利语": "it",
    "意大利文": "it",
    "韩语": "kor",
    "韩文": "kor",
    "阿拉伯语": "ara",
    "阿拉伯文": "ara",
    "匈牙利语": "hu",
    "匈牙利文": "hu",
    "瑞典语": "swe",
    "瑞典文": "swe",
    "芬兰语": "fin",
    "芬兰文": "fin",
    "荷兰语": "nl",
    "荷兰文": "nl",
    "波兰语": "pl",
    "波兰文": "pl",
    "丹麦语": "dan",
    "丹麦文": "dan",
    "保加利亚语": "bul",
    "保加利亚文": "bul",
    "希腊语": "el",
    "希腊文": "el",
    "爱沙尼亚语": "est",
    "爱沙尼亚文": "est",
    "泰语": "th",
    "泰文": "th",
    "越南语": "vie",
    "越南文": "vie",
    "斯洛文尼亚语": "slo",
    "斯洛文尼亚文": "slo",
    "罗马尼亚语": "rom",
    "罗马尼亚文": "rom",
}


def get_translation(query: str, lang: str) -> str:
    """
    调用百度翻译进行日文翻译
    :param lang: 语言
    :param query: 翻译的内容
    :return:
    """
    _headers = {"Content-Type": "application/x-www-form-urlencoded"}
    salt = "1435660288"
    sign_raw = f"20231223001919435{query}{salt}sCAog1XZepdaQmhflyWm"
    md5 = hashlib.md5()
    md5.update(sign_raw.encode('utf-8'))
    sign = md5.hexdigest()
    print(sign)
    with requests.session() as sess:
        resp = sess.get(
            f"http://api.fanyi.baidu.com/api/trans/vip/translate?q={query}&from=auto&to={lang}&appid=20231223001919435&salt={salt}&sign={sign}",
            headers=_headers,
            timeout=60,
        )
    if resp.status_code == 200:
        resp_json = json.loads(resp.text)
        result = resp_json["trans_result"][0]["dst"]
        result = result.replace("先生", "せんせい")
        result = result.replace("パパパパ", "パンパカパーン！")
        result = result.replace("ボンボン", "パンパカパーン！")
        result = result.replace("カトパンカトパン", "パンパカパーン！")
        result = result.replace("パンパカパーンカパン", "パンパカパーン！")
        result = result.replace("RPG", "アールピージー")
        result = result.replace("HP", "エイチピー")
        result = result.replace("桃井さん", "モモイ")
        result = result.replace("桃ちゃん", "モモイ")
        result = result.replace("緑ちゃん", "ミドリ")
        result = result.replace("緑さん", "ミドリ")
        result = result.replace("みどりちゃん", "ミドリ")
        result = result.replace("ゆずさん", "ユズ")
        result = result.replace("優香さん", "ユウカ")
        result = result.replace("優香", "ユウカ")
        result = result.replace("孥", "ヌ")
        result = result.replace("日鞠", "ヒマリ")
        result = result.replace("日奈", "ヒナ")
        result = result.replace("Kei", "ケイー")
        result = result.replace("kei", "ケイー")
        result = result.replace("真理部", "ヴェリタス")
        result = result.replace("にゃっほ", "にゃ")
        result = result.replace("歌赫娜学院", "ゲヘナ学園")
        result = result.replace("歌赫娜", "ゲヘナ")
        return result
    else:
        return "エラー発生!!!"


def get_audio(line: str) -> str:
    """
    通过VITS获取语音，返回文件名
    :return:
    """
    print(line)
    _headers = {"Content-Type": "application/json"}
    with requests.session() as sess:
        resp = sess.get(
            f" http://127.0.0.1:23456/voice/bert-vits2?text={line}&id=0&format=silk&emotion=0&lang=ja",
            headers=_headers,
            timeout=60,
        )
    if resp.status_code == 200:
        with open(voice_file_name, "wb") as file:
            file.write(resp.content)
        return "voice/alice.silk"
    else:
        return ""


def voice_bert_vits2(text, id=0, format="wav", lang="auto", length=1, noise=0.667, noisew=0.8, segment_size=50, sdp_ratio=0.2,
                     save_audio=True, save_path=None):
    fields = {
        "text": text,
        "id": str(id),
        "format": format,
        "lang": lang,
        # "length": str(length),
        "noise": str(noise),
        "noisew": str(noisew),
        "segment_size": str(segment_size),
        "sdp_ratio": str(sdp_ratio)
    }
    boundary = '----VoiceConversionFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))

    m = MultipartEncoder(fields=fields, boundary=boundary)
    headers = {"Content-Type": m.content_type}
    url = "http://127.0.0.1:23456/voice/bert-vits2"

    res = requests.post(url=url, data=m, headers=headers)
    if save_audio:
        with open(voice_file_name, "wb") as f:
            f.write(res.content)
        print(voice_file_name)
        return voice_file_name
    return ""


def voice_gpt_sovits(text, id=0, format="wav", lang="auto", preset="default", save_audio=True, save_path=None):
    fields = {
        "text": text,
        "id": str(id),
        "format": format,
        "lang": lang,
        "preset": preset
    }
    boundary = '----VoiceConversionFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))

    m = MultipartEncoder(fields=fields, boundary=boundary)
    headers = {"Content-Type": m.content_type}
    url = "http://127.0.0.1:23456/voice/gpt-sovits"

    res = requests.post(url=url, data=m, headers=headers)
    if save_audio:
        with open(voice_file_name, "wb") as f:
            f.write(res.content)
        print(voice_file_name)
        return voice_file_name
    return ""


def gradio_bert_vits2(text):
    status, file_url = get_audio_from_gradio(text)
    print(file_url)
    return file_url


def voice_generate(text, format="silk", lang="auto"):
    # return voice_gpt_sovits(text, format=format, lang=lang)
    # return voice_bert_vits2(text, format=format, lang=lang)
    return gradio_bert_vits2(text)


def get_audio_auto(line: str) -> str:
    """
    通过VITS获取语音，返回文件名
    :return:
    """
    print(line)
    _headers = {"Content-Type": "application/json"}
    with requests.session() as sess:
        resp = sess.get(
            f" http://127.0.0.1:23456/voice/bert-vits2?text={line}&id=0&format=silk&emotion=0&lang=auto&length_zh=1&length_en=1",
            headers=_headers,
            timeout=60,
        )
    if resp.status_code == 200:
        with open(voice_file_name, "wb") as file:
            file.write(resp.content)
        return "voice/alice.silk"
    else:
        return ""


def remove_action(line: str) -> str:
    """
    去除括号里描述动作的部分（要求AI输出格式固定）
    :param line:
    :return:
    """
    line = line.replace("(", "（")
    line = line.replace(")", "）")
    pattern = r'\（[^\（^\）]*\）'
    match = re.findall(pattern, line)
    if len(match) == 0:
        return line
    else:
        for i in range(len(match)):
            print(match[i])
            line = line.replace(match[i], "")
        return line


@speaker.handle()
async def speak(event: GroupMessageEvent):
    line = str(event.message).replace("/说话 ", "")
    await speaker.send(MessageSegment.voice(voice_generate(line)))


@translator.handle()
async def translate(event: GroupMessageEvent):
    line = str(event.message).replace("/翻译", "")
    lines = line.strip().split(" ")
    print(lines)
    if len(lines) == 1:
        await translator.send(get_translation(line, "zh"))
    else:
        lang = lines[0]
        print(lang)
        lang_code = lang_codes.get(lang)
        if lang_code is  None:
            await translator.send("不支持的语言。")
        else:
            processed_line = line.replace(lang, "").strip()
            await translator.send(get_translation(processed_line, lang_code))


@test_amr.handle()
async def test(event: GroupMessageEvent):
    await test_amr.send(MessageSegment.voice("voice/alice.amr"))





