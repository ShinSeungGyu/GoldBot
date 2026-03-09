import requests
from dotenv import load_dotenv
import os

API_KEY = f"Bearer {os.getenv('LOSTARK_API_KEY')}"

def get_gold_islands():
    url = 'https://developer-lostark.game.onstove.com/gamecontents/calendar'
    headers = {'accept': 'application/json', 'authorization': API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        for i in data:
            if i["CategoryName"] == "모험 섬":
                reward = i["RewardItems"]
                for r in reward:
                    itemList = r["Items"]
                    for item in itemList:
                        print(item)
                    print("-----------------")
        gold_islands = []
        
        # API 응답 데이터 중 오늘 날짜의 '모험 섬' 중 보상에 '골드'가 포함된 항목 필터링
        # (실제 API 구조에 맞춘 파싱 로직 필요)
        return gold_islands
    return None

get_gold_islands()