from src.plugins.comfyUI import get_images, prompt_text, server_address, client_id
import websocket
import random
import json
from nonebot import on_command
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.red.event import GroupMessageEvent

master_id = "664648216"

painting_call = on_command("绘图 ")
advanced_painting_call = on_command("高级绘图 ")


@painting_call.handle()
async def painting(event: GroupMessageEvent):
    """
    调用ComfyUI绘图
    :param event:
    :return:
    """
    user_id = event.senderUin
    positive_tags = str(event.message).replace("/绘图 ", "")
    print(positive_tags)
    group_id = event.group_id
    if user_id == master_id or group_id == "739048999":
        prompt = json.loads(prompt_text)
        # set the text prompt for our positive CLIPTextEncode
        prompt["6"]["inputs"]["text"] = positive_tags
        # set the text prompt for our negative CLIPTextEncode
        prompt["7"]["inputs"]["text"] = "aidxlv05_neg blurry, low contrast, {bad hands, bad feet}, lowres, ugly"

        # set the seed for our KSampler node
        seeds = random.randint(0, 18446744073709551615)
        prompt["3"]["inputs"]["seed"] = seeds
        prompt["4"]["inputs"]["ckpt_name"] = "animeIllustDiffusion_v052.safetensors"

        ws = websocket.WebSocket()
        ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
        images = get_images(ws, prompt)
        with open("sd_gen/alice_gen.png", "wb") as file:
            file.write(images['9'][0])
        await painting_call.send(MessageSegment.image("sd_gen/alice_gen.png") + "seeds=" + str(seeds))
    else:
        await painting_call.send("权限不允许。")


def process_for_params(raw_message: str) -> dict:
    params: dict = {}
    raw_message_list = raw_message.split(";")
    for i in range(len(raw_message_list)):
        if "positive prompt:" in raw_message_list[i]:
            params["positive"] = raw_message_list[i].replace("positive prompt:", "").strip()
        if "negative prompt:" in raw_message_list[i]:
            params["negative"] = raw_message_list[i].replace("negative prompt:", "").strip()
        if "size:" in raw_message_list[i]:
            size = raw_message_list[i].replace("size:", "").strip().split("*")
            params["height"] = int(size[0])
            params["width"] = int(size[1])
        if "seeds:" in raw_message_list[i]:
            seeds = raw_message_list[i].replace("seeds:", "").strip()
            if seeds != "-1":
                params["seeds"] = int(seeds)
        if "model:" in raw_message_list[i]:
            params["model"] = raw_message_list[i].replace("model:", "").strip()
        if "steps:" in raw_message_list[i]:
            params["steps"] = int(raw_message_list[i].replace("steps:", "").strip())
        if "cfg:" in raw_message_list[i]:
            params["cfg"] = float(raw_message_list[i].replace("cfg:", "").strip())
        if "denoise:" in raw_message_list[i]:
            params["denoise"] = float(raw_message_list[i].replace("denoise:", "").strip())
        if "sampler:" in raw_message_list[i]:
            params["sampler"] = raw_message_list[i].replace("sampler:", "").strip()
    return params


@advanced_painting_call.handle()
async def advanced_painting(event: GroupMessageEvent):
    """
    调用ComfyUI进行高级绘图（设定positive prompt,negative prompt,seeds,size等参数）
    格式如下：
    positive prompt: ... ; negative prompt: ... ; seeds: ... (-1时为random); size: height*width; model: model_name; steps:...; cfg:...; denoise:...; sampler: ...
    示例：
    positive prompt: masterpiece best quality girl; negative prompt: aidxlv05_neg blurry, low contrast, {bad hands, bad feet}; seed: -1; size: 1024*1024; model: animeIllustDiffusion_v052.safetensors;
        steps:30; cfg:7; denoise:1; sampler: euler
    :param event:
    :return:
    """
    raw_message = str(event.message).replace("/高级绘图 ", "")
    if raw_message == "help":
        await advanced_painting_call.send("""格式如下：
    positive prompt: ... ; negative prompt: ... ; seeds: ... (-1时为random); size: height*width; model: model_name; steps:...; cfg:...; denoise:...; sampler: ...
    示例：
    positive prompt: masterpiece best quality girl; negative prompt: aidxlv05_neg blurry, low contrast, {bad hands, bad feet}; seeds: -1; size: 1024*1024; model: animeIllustDiffusion_v052.safetensors;
    steps:30; cfg:7; denoise:1; sampler: euler
    model list: 'abyssorangemix3AOM3_aom3a1b.safetensors', 'animeIllustDiffusion_v052.safetensors', 'artErosAerosATribute_aerosNovae.safetensors', 'chilloutmix_NiPrunedFp32Fix.safetensors', 'furnace1011_furnace11.safetensors', 'furnace34_furnace34.safetensors', 'pastelMixStylizedAnime_pastelMixPrunedFP16.safetensors', 'sdXL_v10VAEFix.safetensors', 'tmndMix_tmndMixPlus.safetensors'""")
    else:
        user_id = event.senderUin
        group_id = event.group_id
        if user_id == master_id or group_id == "739048999":
            params: dict = process_for_params(raw_message)
            print(params)
            if params.get("positive") is None:
                positive_prompt = "masterpiece best quality girl"
            else:
                positive_prompt = params.get("positive")
            if params.get("negative") is None:
                negative_prompt = "aidxlv05_neg blurry, low contrast, {bad hands, bad feet}, lowres, ugly"
            else:
                negative_prompt = params.get("negative")
            if params.get("seeds") is None:
                seeds = random.randint(0, 18446744073709551615)
            else:
                seeds = params.get("seeds")
            if params.get("height") is None:
                height = 1024
            else:
                height = params.get("height")
            if params.get("width") is None:
                width = 1024
            else:
                width = params.get("width")
            if params.get("model") is None:
                model = "animeIllustDiffusion_v052.safetensors"
            else:
                model = params.get("model")
            if params.get("steps") is None:
                steps = 30
            else:
                steps = params.get("steps")
            if params.get("cfg") is None:
                cfg = 0.7
            else:
                cfg = params.get("cfg")
            if params.get("denoise") is None:
                denoise = 1
            else:
                denoise = params.get("denoise")
            if params.get("sampler") is None:
                sampler = "euler"
            else:
                sampler = params.get("sampler")

            prompt = json.loads(prompt_text)
            prompt["6"]["inputs"]["text"] = positive_prompt
            prompt["7"]["inputs"]["text"] = negative_prompt
            prompt["3"]["inputs"]["seed"] = seeds
            prompt["5"]["inputs"]["height"] = height
            prompt["5"]["inputs"]["width"] = width
            prompt["4"]["inputs"]["ckpt_name"] = model
            prompt["3"]["inputs"]["steps"] = steps
            prompt["3"]["inputs"]["cfg"] = cfg
            prompt["3"]["inputs"]["denoise"] = denoise
            prompt["3"]["inputs"]["sampler_name"] = sampler
            ws = websocket.WebSocket()
            ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
            images = get_images(ws, prompt)
            with open("sd_gen/alice_gen.png", "wb") as file:
                file.write(images['9'][0])
            await painting_call.send(MessageSegment.image("sd_gen/alice_gen.png") + "seeds=" + str(seeds))
        else:
            await painting_call.send("权限不允许。")
