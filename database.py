import redis    # 导入redis 模块
from common import LASTEST, TOPICS, GET_NEWS_FAST

pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def store_news():
    # 最新 10 篇新聞
    r.set("lastest", str(GET_NEWS_FAST(LASTEST, 5)))

    # 每個主題 5 篇新聞
    for key, value in TOPICS.items():
        r.set(key, str(GET_NEWS_FAST(value, 5)))

    print("[完成] 更新新聞資料")
