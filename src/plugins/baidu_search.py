from nonebot import on_command
from nonebot.adapters.red.message import MessageSegment
from nonebot.adapters.red.event import GroupMessageEvent
from playwright.async_api import async_playwright
import playwright
import time
import asyncio


def _checker(event: GroupMessageEvent) -> bool:
    return event.to_me


baidu_screenshot = on_command("百度 ")
baidubaike_screenshot = on_command("百科 ")
net_screenshot = on_command("访问 ")
wiki_screenshot = on_command("维基 ")
wiktionary_screenshot = on_command("词典 ")


@baidu_screenshot.handle()
async def baidu(event: GroupMessageEvent):
    info = str(event.message).replace("/百度 ", "")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.baidu.com/s?ie=UTF-8&wd="+info)
        await page.screenshot(path=f"screenshots/baidu_{info}.png", full_page=True)
        await browser.close()
    await baidu_screenshot.send(MessageSegment.image(f"screenshots/baidu_{info}.png"))


@baidubaike_screenshot.handle()
async def baike(event: GroupMessageEvent):
    info = str(event.message).replace("/百科 ", "")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://baike.baidu.com/item/"+info)
        await page.screenshot(path=f"screenshots/baike_{info}.png", full_page=True)
        await browser.close()
    await baidubaike_screenshot.send(MessageSegment.image(f"screenshots/baike_{info}.png"))


@wiki_screenshot.handle()
async def wiki(event: GroupMessageEvent):
    info = str(event.message).replace("/维基 ", "")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://en.wikipedia.org/wiki/"+info)
        await page.screenshot(path=f"screenshots/wiki_{info}.png", full_page=True)
        await browser.close()
    await wiktionary_screenshot.send(MessageSegment.image(f"screenshots/wiki_{info}.png"))


@wiktionary_screenshot.handle()
async def wiktionary(event: GroupMessageEvent):
    info = str(event.message).replace("/词典 ", "")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://en.wiktionary.org/wiki/" + info)
        await page.screenshot(path=f"screenshots/wiktionary_{info}.png", full_page=True)
        await browser.close()
    await wiki_screenshot.send(MessageSegment.image(f"screenshots/wiktionary_{info}.png"))


@net_screenshot.handle()
async def show_page(event: GroupMessageEvent):
    if_error = False
    url = str(event.message).replace("/访问 ", "")
    print(url)
    current_time = time.time()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        title = await page.title()
        try:
            await page.goto(url)
            await page.screenshot(path=f"screenshots/{title}.png", full_page=True)
        except playwright._impl._errors.Error:
            if_error = True
        await browser.close()
    if not if_error:
        await net_screenshot.send(MessageSegment.image(f"screenshots/{title}.png"))
    else:
        await net_screenshot.send("抱歉，访问错误~~~")

