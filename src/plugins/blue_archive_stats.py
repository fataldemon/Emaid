import json
import os

from nonebot import on_command
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.red.event import GroupMessageEvent
import requests
import random
import datetime
from src.skills.user_status_process import get_user_status, set_tarot_date

date_format = "%Y-%m-%d"

ba_stats = on_command("攻略 ")
tarots = on_command("塔罗牌")
gacha = on_command("抽卡")

star1_student = ["千夏", "春香", "朱莉", "小玉", "明日奈", "琴里", "菲娜", "铃美", "志美子", "芹娜", "好美"]
star2_student = ["明里", "纯子", "睦月", "佳代子", "风香", "优香", "茜", "晴", "歌原", "千世", "椿", "芹香", "绫音", "莲见", "花江", "爱理", "静子", "桃井", "花子", "桐乃", "玛丽"]
star3_student = ["日奈", "伊织", "晴奈", "泉", "爱露", "堇", "艾米", "花凛", "尼禄", "真纪", "响", "纱绫", "瞬", "白子", "星野",
                 "日富美", "鹤城", "真白", "泉奈", "绿", "爱丽丝", "柚子", "切里诺", "梓", "小春", "日富美（泳装）", "白子（骑行）",
                 "瞬（幼）", "纱绫（便服）", "夏", "亚子", "切里诺（温泉）", "千夏（温泉）", "和香（温泉）", "阿露（新春）", "睦月（新春）",
                 "日奈（泳装）", "伊织（泳装）", "芹香（新春）", "若藻"]
star3_png = ["hina.png", "iyori.png", "haruna.png", "izumi.png", "aru.png", "sumire.png", "eimi.png", "karin.png", "neru.png", "maki.png", "hibiki.png", "saya.png", "shun.png", "shiroko.png", "hoshino.png",
             "hifumi.png", "tsurugi.png", "mashiro.png", "izuna.png", "midori.png", "arisu.png", "yuzu.png", "cherino.png", "azusa.png", "koharu.png", "hifumi(swim).png", "shiroko(ride).png",
             "shun(kid).png", "saya(casual).png", "natsu.png", "ako.png", "cherino(hot spring).png", "chinatsu(hot spring).png", "nodoka(hot spring).png", "aru(spring).png", "mutsuki(spring).png",
             "hina(swim).png", "iori(swim).png", "serika(spring).png", "wakamo.png"]

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


@tarots.handle()
async def get_tarots(event: GroupMessageEvent):
    """
    随机塔罗牌
    :param event:
    :return:
    """
    refresh_token = False
    current_time = datetime.datetime.now()
    user_status = get_user_status(event.senderUin)
    last_tarot_str = user_status.get("last_tarot_day")
    last_tarot_num = user_status.get("last_tarot_result")
    file_list = os.listdir("ba_stats/tarots")
    if last_tarot_str is None:
        refresh_token = True
    else:
        last_tarot_date = datetime.datetime.strptime(last_tarot_str, date_format)
        duration = current_time - last_tarot_date
        if duration.days >= 1:
            refresh_token = True
        elif current_time.date() != last_tarot_date.date():
            refresh_token = True
    if refresh_token:
        rand = random.randint(0, len(file_list)-1)
        print(f"共有{len(file_list)}张塔罗牌。")
        set_tarot_date(event.senderUin, current_time.strftime(date_format), rand)
        await tarots.send(MessageSegment.image(f"ba_stats/tarots/{file_list[rand]}"))
    else:
        await tarots.send(MessageSegment.image(f"ba_stats/tarots/{file_list[last_tarot_num]}") + "今天已经抽取过了，结果是这张。明天再试试吧~~")


@gacha.handle()
async def try_gacha(event: GroupMessageEvent):
    """
    十连抽卡
    :param event:
    :return:
    """
    mark = ""
    result = ""
    img = ""
    bottom = True
    for i in range(10):
        rand = random.randint(1, 1000)
        if i == 5:
            mark += '\n'
        if rand <= 30:
            rand2 = random.randint(0, len(star3_student)-1)
            result += "★3-" + star3_student[rand2] + " "
            mark += "🌈"
            img += MessageSegment.image(f"ba_stats/gacha/{star3_png[rand2]}")
            bottom = False
        elif rand <= 215:
            rand2 = random.randint(0, len(star2_student)-1)
            result += "★2-" + star2_student[rand2] + " "
            mark += "🟨"
            bottom = False
        else:
            if i == 9 and bottom:
                rand2 = random.randint(0, len(star2_student) - 1)
                result += "★2-" + star2_student[rand2] + " "
                mark += "🟨"
                bottom = False
            else:
                rand2 = random.randint(0, len(star1_student)-1)
                result += "★1-" + star1_student[rand2] + " "
                mark += "🟦"
    await gacha.send(mark + "\n您的十连结果为：" + result + "\n" + img)
