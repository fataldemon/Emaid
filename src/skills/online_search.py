import time
import traceback

from playwright.async_api import async_playwright
import asyncio


async def online_search_func(item: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        pages = []
        await page.goto("https://www.bing.com/search?q="+item)
        time.sleep(1)
        # 打印网页源代码
        url_list = await page.query_selector_all(".b_algo >> .tilk")
        summary_list = await page.query_selector_all(".b_algo >> .b_algoSlug")
        info = ""
        page_no = 0
        moegirl_token = False
        baike_token = False
        wiki_token = False
        for i in url_list:
            url = await i.get_attribute("href")
            if page_no >= 2 or (moegirl_token and baike_token):
                break
            try:
                if url.startswith("https://zh.moegirl.org.cn") and (not moegirl_token):
                    pages.append(await browser.new_page())
                    await pages[page_no].goto(url)
                    time.sleep(1)
                    box_locator = await pages[page_no].query_selector(".mw-parser-output >> .moe-infobox")
                    box_content = await box_locator.text_content()
                    box_content = box_content.replace("\n\n\n", "")
                    info += f"根据{url}网站提供的信息如下：\n{box_content}\n"
                    context_locator = await pages[page_no].query_selector_all(
                        ".mw-parser-output > h2:not(table *), .mw-parser-output > h3:not(table *), "
                        ".mw-parser-output > h4:not(table *), .mw-parser-output > p:not(table *), "
                        ".mw-parser-output > ul:not(table *)")
                    for item in context_locator:
                        search_info = await item.text_content()
                        search_info = search_info.replace("\n\n", "")
                        info += search_info + "\n"
                    page_no += 1
                    moegirl_token = True
                elif url.startswith("https://baike.baidu") and (not baike_token):
                    pages.append(await browser.new_page())
                    await pages[page_no].goto(url)
                    time.sleep(1)
                    # context_locator = await pages[page_no].query_selector(".lemmaSummary_c2Xg9")
                    context_locator = await pages[page_no].query_selector(".J-summary")
                    summary = await context_locator.text_content()
                    box_locator = await pages[page_no].query_selector(".J-basic-info")
                    brief_info = await box_locator.text_content()
                    info += f"根据{url}网站提供的信息如下：\n{brief_info}\n{summary}\n"
                    page_no += 1
                    baike_token = True
                # elif url.startswith("https://zh.wikipedia.org") or url.startswith("https://en.wikipedia.org"):
                #     pages.append(await browser.new_page())
                #     await pages[page_no].goto(url)
                #     time.sleep(1)
                #     context_locator = await pages[page_no].query_selector_all(
                #         ".mw-parser-output > h2:not(table *), .mw-parser-output > h3:not(table *), "
                #         ".mw-parser-output > h4:not(table *), .mw-parser-output > p:not(table *), "
                #         ".mw-parser-output > ul:not(table *)")
                #     for item in context_locator:
                #         search_info = await item.text_content()
                #         print(search_info.replace("\n\n", ""))
                #     page_no += 1
            except Exception as e:
                traceback.print_exc()
                info += f"地址{url}上或许能得到有用的信息，但是目前无法访问......\n"
        info += f"其他网站的摘要信息：\n"
        for summary_item in summary_list:
            info += await summary_item.text_content()
            info += "\n"
        await browser.close()
        return info


if __name__ == "__main__":
    info = asyncio.run(online_search_func("早濑优香"))
    print(info)
