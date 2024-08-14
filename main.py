from openai import OpenAI
import requests
from datetime import datetime
import time

from common import LASTEST, TOPICS, GET_NEWS_FAST, FORMAT_RESPONSE, FORMAT_NEWS, DB_LASTEST
from database import r, store_news
import random
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

def call_function_by_name(function_name, function_args):
    global_symbols = globals()

    # 檢查 function 是否存在＆可用
    if function_name in global_symbols and callable(global_symbols[function_name]):
        # 呼叫
        function_to_call = global_symbols[function_name]
        return function_to_call(**function_args)
    else:
        # 丟出錯誤
        raise ValueError(f"Function '{function_name}' not found or not callable.")
  
# my functions
def get_latest_news(top=3):
  result = eval(r.get(DB_LASTEST))
  if len(result) < top:
     return GET_NEWS_FAST(LASTEST, top)
  return random.sample(result, top if len(result)>=top else len(result))  

def get_recommand_news(topic, top=3):
  result = eval(r.get(topic))
  if len(result) < top:
     return GET_NEWS_FAST(TOPICS[topic], top)
  return random.sample(result, top if len(result)>=top else len(result))

def get_topic_news(topic, top=3):
  url = f'https://news.google.com/search?q={topic.replace(" ", "%20")}&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant'
  return GET_NEWS_FAST(url, top)

# define functions
functions = [
  {
    "name": "get_topic_news",
    # "description": "Search for relevant news reports or information based on a specific topic",
    "description": "依關鍵字搜尋新聞，只要是問題，都會呼叫這個函式",
    "parameters": {
      "type": "object",
      "properties": {
        "topic": {
          "type": "string",
          "description": "The topic of news reports, e.g. 寶林茶室中毒"
        }
      },
      "required": ["topic"],
    }
  },
  {
    "name": "get_latest_news",
    # "description": "Search for latest news reports without specific topic",
    "description": "獲得最新新聞",
    "parameters": {
      "type": "object",
      "properties": {
        "top": {
          "type": "number",
          "description": "The number of latest news that user wants to watch, e.g. 3"
        }
      },
      "required": [],
    }
  },
  {
    "name": "get_recommand_news",
    # "description": "Search for the recommand news with specific topic",
    "description": "依主題搜尋新聞",
    "parameters": {
      "type": "object",
      "properties": {
        "top": {
          "type": "number",
          "description": "The number of latest news that user wants to watch, e.g. 3"
        },
        "topic": {
          "type": "string",
          "description": "Topic can only be one of the following: taiwan, global, local, business, science_technology, entertainment, pe, healthy，如果是其他的關鍵字，則須當作關鍵字來搜尋"
        }
      },
      "required": ["topic"],
    }
  }
]

client = OpenAI()

# messages = []

# flask
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

@app.route('/greeting', methods=['GET'])
def greeting():
  res = []
  res.append(FORMAT_RESPONSE("text", {
    "tag" : "span",
    "content" : f"您好～ 我是新聞小助手，我能夠提供以下功能:"
  }))

  res.append(FORMAT_RESPONSE("button", {
    "content": "最新新聞",
    "function": "get_latest_news"
  }))

  res.append(FORMAT_RESPONSE("button", {
    "content": "依類別推薦新聞",
    "function": "get_recommand_news"
  }))

  res.append(FORMAT_RESPONSE("button", {
    "content": "依關鍵字搜尋新聞",
    "function": "get_topic_news"
  }))

  return jsonify({
    "response": res
  })

@app.route('/chat', methods=['POST'])
def chat_with_bot():
  start_time = time.time()
  res = []

  data = request.json  # 拿到送來的參數
  if 'user' not in data:
    return jsonify({'error': "Didn't receive what user said"}), 400
  
  messages = [{
    "role": "user",
    "content": data["user"]
  }]

  response = client.chat.completions.create(
    model="gpt-3.5-turbo", 
    messages= messages,
    functions = functions
  )

  res_mes = response.choices[0].message
  content = res_mes.content
  function_call = res_mes.function_call

  print(f"function_call: {function_call}")

  # gpt 直接回覆
  if content != None:
    # print(f"機器人1: {content}")
    res.append(FORMAT_RESPONSE("text", {
      "tag" : "span",
      "content" : content
    }))
    
    return jsonify({
      'response': res
    })
  
  if function_call: # 需要呼叫 function
    print(f"呼叫函式的名稱: {function_call.name}")
    print(f"呼叫函式的參數: {function_call.arguments}")

    data = call_function_by_name(function_call.name, eval(function_call.arguments))
    print(f"最終結論: {data}")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f">>>>>>>> 本輪對話花費時間: {execution_time}")
    
    return jsonify({'response': FORMAT_NEWS(data)})

@app.route('/set', methods=['POST'])
def set_key():
    key = request.json.get('key')
    value = request.json.get('value')
    r.set(key, value)
    return jsonify({"message": "Key set successfully"})

@app.route('/get', methods=['GET'])
def get_key():
    key = request.args.get('key')
    value = r.get(key)
    if value is None:
        return jsonify({"message": "Key not found"}), 404
    return jsonify({"key": key, "value": value})

@app.route('/start_collect', methods=['GET'])
def apscheduler():
  # 配置 APScheduler
  scheduler = BackgroundScheduler()
  scheduler.start()

  # 启动时立即执行一次 store_news 函数
  store_news()

  # 每 60 分钟执行一次 store_news 函数
  scheduler.add_job(
      func=store_news,
      trigger=IntervalTrigger(minutes=60),
      id='store_news_job',
      name='Store news every 60 minutes',
      replace_existing=True
  )

  # 当应用退出时，关闭 APScheduler
  atexit.register(lambda: scheduler.shutdown())

  return jsonify({
    "response": "更新完畢"
  })

if __name__ == '__main__':
    app.run(debug=True)

# while(True):
#   user_input = input("使用者: ")
#   messages = [{
#     "role": "user",
#     "content": user_input
#   }]

#   # messages.append({
#   #   "role": "user",
#   #   "content": user_input
#   # })
  
#   start_time = time.time()

#   response = client.chat.completions.create(
#     model="gpt-3.5-turbo", 
#     messages= messages,
#     functions = functions
#   )

#   res_mes = response.choices[0].message
#   content = res_mes.content
#   function_call = res_mes.function_call

#   # print(f"res_mes: {res_mes}")
#   print(f"function_call: {function_call}")

#   # gpt 直接回覆
#   if content != None:
#     print(f"機器人1: {content}")
  
#   if function_call: # 需要呼叫 function
#     print(f"呼叫函式的名稱: {function_call.name}")
#     print(f"呼叫函式的參數: {function_call.arguments}")

#     data = call_function_by_name(function_call.name, eval(function_call.arguments))
#     print(f"最終結論: {data}")

#     messages.append({
#       "role": "function",
#       "name": function_call.name,
#       "content": str(data)
#     })

#     response = client.chat.completions.create(
#       model="gpt-3.5-turbo", 
#       messages= messages
#     )
#     # print("--------------------")
#     print(f"機器人: {response.choices[0].message.content}")
#     # print("--------------------")
    
#   end_time = time.time()
#   execution_time = end_time - start_time
#   print(f">>>>>>>> 本輪對話花費時間: {execution_time}")