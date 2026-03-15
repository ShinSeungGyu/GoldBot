import os
import requests
import discord
from datetime import time
from discord.ext import tasks
from app import API_KEY, bot


# 경매장 검색
# Acc에 따라 검색(목걸이, 귀걸이, 반지)
# 각 악세 별 상중, 중상, 상상 악세를 검색
# 악세별 힘민지가 다르므로 payload를 악세별로 작성해서 여러번 전송
async def search_lostark_auction(acc, base, option1, value1, option2, value2):
    url = "https://developer-lostark.game.onstove.com/auctions/items"
    headers = {'Content-Type': 'application/json','authorization': API_KEY, 'accept': 'application/json'}
    payload = {
        "ItemLevelMin": 0,
        "ItemLevelMax": 0,
        "ItemGradeQuality": 70,
        "ItemUpgradeLevel": None,
        "ItemTradeAllowCount": None,
        "SkillOptions": [
            {
                "FirstOption": None,
                "SecondOption": None,
                "MinValue": None,
                "MaxValue": None
            }
        ],
        "EtcOptions": [
            { #악세별 힘민지 최소값 (목걸이:17000, 귀걸이:13000, 반지:12000 )
                "FirstOption": 1,
                "SecondOption": 11,
                "MinValue": base,
                "MaxValue": None
            },
            # option > 추피:41, 적주피:42, 아덴획득량:43, 낙인력:44 | 공격력 %:45, 무기 공격력 %:46 | 치적:49, 치피:50, 아공강:51, 아피강:52, 
            { 
                "FirstOption": 7, 
                "SecondOption": option1,
                "MinValue": value1,
                "MaxValue": value1
            },
            # value > 추피:160/260, 적주피:120/200, 아덴획득량:360/600, 낙인력:480/800 | 공격력 %:95/155, 무기 공격력 %:180/300 | 치적:95/155, 치피:240/400, 아공강:300/500, 아피강:450/750
            {
                "FirstOption": 7, 
                "SecondOption": option2,
                "MinValue": value2,
                "MaxValue": value2
            }
        ],
        "Sort": "BIDSTART_PRICE",
        "CategoryCode": acc,        #악세별 코드값 ( 목걸이:200010, 귀걸이:200020, 반지:200030 )
        "CharacterClass": "바드",   #임의 직업 지정
        "ItemTier": 4,
        "ItemGrade": "고대",
        "ItemName": None,  # "string" 대신 None을 넣어야 전체 검색이 됩니다.
        "PageNo": 1,        # API는 보통 1페이지부터 시작합니다.
        "SortCondition": "ASC"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # 응답 확인
        if response.status_code == 200:
            result = response.json()
            items = result.get('Items', [])
            
            if not items:
                print("검색된 아이템이 없습니다.")
                return
            else:
                result_strings = []
                item = items[0]
                name = item.get('Name')
                price = item.get('AuctionInfo', {}).get('BuyPrice', '없음')
                result_strings.append(f"💎 {name} | {price}G")
                return result_strings
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"요청 중 오류 발생: {e}")


scheduled_times = [time(hour=h, minute=0, second=0) for h in range(24)]
@tasks.loop(time=scheduled_times)
async def auction_acc():
    print("악세 검색 시작")
    msg =f"📢 현재 딜러 악세 알림!\n"
    deal_search_list = [
        [200010, 17000, 41, 160, 42, 200],  #목걸이 추피중 적주피상
        [200010, 17000, 41, 260, 42, 120],  #목걸이 추피상 적주피중
        [200010, 17000, 41, 260, 42, 200],  #목걸이 추피상 적주피상
        [200020, 13000, 45, 95, 46, 300],   #귀걸이 공%중 무공%상
        [200020, 13000, 45, 155, 46, 180],  #귀걸이 공%상 무공%중
        [200020, 13000, 45, 155, 46, 300],  #귀걸이 공%상 무공%상
        [200030, 12000, 49, 95, 50, 400],   #반지 치적중 치피상
        [200030, 12000, 49, 155, 50, 240],  #반지 치적상 치피중
        [200030, 12000, 49, 155, 50, 400]   #반지 치적상 치피상
    ]
    acc_name_list = [
        "목걸이 추피중 적주피상 : ",
        "목걸이 추피상 적주피중 : ",
        "목걸이 추피상 적주피상 : ",
        "귀걸이 공%중 무공%상 : ",
        "귀걸이 공%상 무공%중 : ",
        "귀걸이 공%상 무공%상 : ",
        "반지 치적중 치피상 : ",
        "반지 치적상 치피중 : ",
        "반지 치적상 치피상 : "
    ]
    for deal_search, acc_name  in zip(deal_search_list, acc_name_list):
        # 리스트 언패킹(*)으로 호출
        acc_list = await search_lostark_auction(*deal_search)
        
        # [수정 포인트] acc_list가 정말 리스트인지, 그리고 비어있지 않은지 확인
        if isinstance(acc_list, list) and len(acc_list) > 0:
            msg += acc_name + "\n".join(acc_list) + "\n"
        elif acc_list is None:
            # 함수가 None을 반환한 경우 예외 처리
            msg += "⚠️ API 응답이 없거나 오류가 발생했습니다.\n"
        else:
            # 검색 결과가 없는 경우 (빈 리스트 등)
            msg += "❌ 조건에 맞는 매물이 없습니다.\n"
            
    for guild in bot.guilds:
        target_channel = discord.utils.get(guild.text_channels, name="알림") #서버의 채널 이름에 "알림"이 포함되어있어야 한다.
        
        if target_channel:
            try:
                await target_channel.send(msg) #목표 채널에 메시지를 전송
            except Exception as e:
                print(f"{guild.name}에 메시지를 보내지 못했습니다: {e}")