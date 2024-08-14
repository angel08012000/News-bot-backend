ARTICLE_CSS_SELECTOR = "c-wiz.PO9Zff.Ccj79.kUVvS, c-wiz.XBspb" #c-wiz.XBspb
LINK_CSS_SELECTOR = "a.gPFEn, a.JtKRv"


LASTEST = "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
TOPICS = {
    "taiwan": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFptTXpJU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "global": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "local": "https://news.google.com/topics/CAAqHAgKIhZDQklTQ2pvSWJHOWpZV3hmZGpJb0FBUAE/sections/CAQiWENCSVNQRG9JYkc5allXeGZkakpDRUd4dlkyRnNYM1l5WDNObFkzUnBiMjV5RGhJTUwyY3ZNWEUxWW14a2JITnFlZzRLREM5bkx6RnhOV0pzWkd4emFpZ0EqNQgAKjEICiIrQ0JJU0dqb0liRzlqWVd4ZmRqSjZEZ29NTDJjdk1YRTFZbXhrYkhOcUtBQVABUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "business": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "science_technology": "https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "entertainment": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNREpxYW5RU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "pe": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFp1ZEdvU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
    "healthy": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNR3QwTlRFU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
}

DB_LASTEST = "lastest"

##### 我是分隔線 #####

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json

from concurrent.futures import ThreadPoolExecutor

def GET_NEWS_FAST(url, top):
    info = GET_NEWS(url, top)
    with ThreadPoolExecutor(max_workers=len(info)) as executor:
        temp = [executor.submit(GET_TEXT_and_SUMMARY, i) for i in info]
        news = [t.result() for t in temp]
    return news

def GET_NEWS(url, top):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    # driver = webdriver.Chrome()
    driver.get(url)

    elements = driver.find_elements(By.CSS_SELECTOR, ARTICLE_CSS_SELECTOR)

    news = []
    topic = ""
    i = 0

    # 打印元素的文本
    for element in elements:
        if i>=top:
            break
        
        try:
            a_tag = element.find_element(By.CSS_SELECTOR, LINK_CSS_SELECTOR)

            topic = a_tag.text
            if len(news)>0 and topic == news[-1]["topic"]:
                continue

            link = a_tag.get_attribute("href").replace("./", "https://news.google.com/")
            news.append({
                "topic": topic,
                "url": link
            })

            # full_text = GET_TEXT(link)
            # summary = GET_SUMMARY_GPT(full_text, topic)

            # news.append({
            #     "topic": topic,
            #     "summary": summary,
            #     "url": link
            # })
            
            i+=1
        except NoSuchElementException:
            continue
    
    driver.quit()
    return news

def GET_TEXT_and_SUMMARY(info):
    try:
        full_text = GET_TEXT(info["url"])
        summary = GET_SUMMARY_GPT(full_text, info["topic"])
        info["summary"] = summary
    except:
        info["summary"] = ""
    return info

def GET_TEXT(url):
    # 拿到網頁裡的文字，過濾標籤
    # res = requests.get(url)
    # full_text =  BeautifulSoup(res.text,'html.parser').get_text()

    # options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    # driver = webdriver.Chrome(options=options)

    # 用 selenium 太慢了
    # driver = webdriver.Chrome()
    # driver.get(url)
    # wait = WebDriverWait(driver, 10)
    # wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    # page_source = driver.page_source

    # # 使用 BeautifulSoup 解析並獲取文本內容
    # soup = BeautifulSoup(page_source, 'html.parser')
    # full_text = soup.get_text()

    # # 關閉瀏覽器
    # driver.quit()

    # return full_text

    # 這個比較快
    response = requests.get(url)
    response.raise_for_status()  # 確保請求成功
    
    soup = BeautifulSoup(response.text, 'html.parser')
    full_text = soup.get_text()
    
    return full_text

def GET_SUMMARY_GPT(full_text, topic):
    client = OpenAI()

    # 請 GPT 幫忙過濾掉無關的文字
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages= [
            {
            "role": "system",
            "content": f"請根據以下內容，幫我摘要出200字以內，以「{topic}」為主題的文章。內容如下：{full_text}"
            }
        ]
    )

    return response.choices[0].message.content

def FORMAT_RESPONSE(key, value):
    with open('./response.json', 'r') as file:
        json_data = file.read()

    res = json.loads(json_data)
    res["ui_type"] = key
    res["data"][key] = value
    return res

def FORMAT_NEWS(news):
    res = []
    for i in range(len(news)):
        res.append(FORMAT_RESPONSE("link", {
            "url" : news[i]["url"],
            "content" : f"({i+1}) {news[i]['topic']}"
        }))
        
        if len(news[i]['summary'])>0:
            res.append(FORMAT_RESPONSE("text", {
                "tag" : "span",
                "content" : news[i]['summary']
            }))
        

        # res.append(FORMAT_RESPONSE("text", {
        #     "tag" : "span",
        #     "content" : f"({i+1}) {news[i]['topic']}\n{news[i]['summary']}"
        # }))
        # res.append(FORMAT_RESPONSE("link", {
        #     "url" : news[i]["url"],
        #     "content" : f"資料來源"
        # }))
    return res

# print(GET_NEWS_FAST(LASTEST, 3))