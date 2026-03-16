import requests
import discord
from database import AuctionDB
from datetime import time
from discord.ext import tasks, commands
from config import API_KEY

    # 경매장 검색
    # Acc에 따라 검색(목걸이, 귀걸이, 반지)
    # 각 악세 별 상중, 중상, 상상 악세를 검색
    # 악세별 힘민지가 다르므로 payload를 악세별로 작성해서 여러번 전송
async def search_lostark_auction(acc, base, option1, value1, option2, value2, option3, value3):
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
            # value > 추피:260, 적주피:200, 아덴획득량:600, 낙인력:800 | 공격력 %:155, 무기 공격력 %:300 | 치적:155, 치피:400, 아공강:500, 아피강:750
            {
                "FirstOption": 7, 
                "SecondOption": option2,
                "MinValue": value2,
                "MaxValue": value2
            },
            {   #딜러:공+(53/390) / 서폿:무공+(54/960), 최생+(55/6500)
                "FirstOption": 7, 
                "SecondOption": option3,
                "MinValue": value3,
                "MaxValue": value3
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
    
        if response.status_code == 200:
            result = response.json()
            items = result.get('Items', [])
            
            if not items:
                print("검색된 아이템이 없습니다.")
                # 매물이 없으므로 이름은 유지하되 가격은 0으로 반환하거나 None 반환
                return {"name": "검색 결과 없음", "price": 0}
            
            # 첫 번째 아이템(최저가) 정보만 추출
            item = items[0]
            name = item.get('Name')
            # BuyPrice가 없으면 0으로 설정
            price = item.get('AuctionInfo', {}).get('BuyPrice', 0)
            
            # 리스트가 아닌 필요한 정보만 딱 담아서 반환
            return {"name": name, "price": price}

        else:
            print(f"Error: {response.status_code}")
            return None

    except Exception as e:
        print(f"요청 중 오류 발생: {e}")
        return None


class AuctionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 여기서 AuctionDB를 생성하여 self.db에 할당합니다.
        # 이렇게 하면 이 클래스 안의 모든 함수에서 self.db를 쓸 수 있습니다.
        self.db = AuctionDB("lostark_auction.db")
        self.auction_acc.start()
        
    scheduled_times = [time(hour=h, minute=0, second=0) for h in range(24)]
    @tasks.loop(time=scheduled_times)
    async def auction_acc(self):
        print("악세 검색 시작")
        deal_search_list = [
            [200010, 17000, 41, 260, 42, 200, 53, 390],  #목걸이 추피상 적주피상 공+상
            [200010, 15178, 41, 260, 42, 200, 53, 390],  #목걸이 추피상 적주피상 공+상 (최저가)
            #----------------------------------------------------------------------------------
            [200020, 13000, 45, 155, 46, 300, 53, 390],  #귀걸이 공%상 무공%상 공+상
            [200020, 11806, 45, 155, 46, 300, 53, 390],  #귀걸이 공%상 무공%상 공+상 (최저가)
            #----------------------------------------------------------------------------------
            [200030, 12000, 49, 155, 50, 400, 53, 390],   #반지 치적상 치피상 공+상
            [200030, 10962, 49, 155, 50, 400, 53, 390]   #반지 치적상 치피상 공+상 (최저가)
        ]
        deal_acc_name_list = [
            "목걸이 상상상",
            "목걸이 상상상(힘민지 최저)",
            "귀걸이 상상상",
            "귀걸이 상상상(힘민지 최저)",
            "반지 상상상",
            "반지 상상상(힘민지 최저)"
        ]
        heal_search_list = [
            [200010, 17000, 43, 600, 44, 800, 54, 960],     #목걸이 상상 무공+상
            [200010, 15178, 43, 600, 44, 800, 54, 960],     #목걸이 상상 무공+상 (최저가)
            [200010, 17000, 43, 600, 44, 800, 55, 6500],    #목걸이 상상 최생+상
            [200010, 15178, 43, 600, 44, 800, 55, 6500],    #목걸이 상상 최생+상 (최저가)
            #----------------------------------------------------------------------------------
            [200020, 13000, 46, 300, 54, 960, 55, 6500],    #귀걸이 공%상 무공+상 최생+상
            [200020, 11806, 46, 300, 54, 960, 55, 6500],    #귀걸이 공%상 무공+상 최생+상 (최저가)
            #----------------------------------------------------------------------------------
            [200030, 12000, 51, 500, 52, 750, 54, 960],     #반지 상상 무공+상
            [200030, 10962, 51, 500, 52, 750, 54, 960],     #반지 상상 무공+상 (최저가)
            [200030, 12000, 51, 500, 52, 750, 55, 6500],    #반지 상상 최생+상
            [200030, 10962, 51, 500, 52, 750, 55, 6500]    #반지 상상 최생+상 (최저가)
        ]
        heal_acc_name_list = [
            "목걸이 상상 무공+",
            "목걸이 상상 최생+(힘민지 최저)",
            "목걸이 상상 최생+",
            "목걸이 상상 최생+(힘민지 최저)",
            "귀걸이 상 무공+상 최생+상",
            "귀걸이 상 무공+상 최생+상(힘민지 최저) : ",
            "반지 상상 무공+상",
            "반지 상상 무공+상(힘민지 최저)",
            "반지 상상 최생+상",
            "반지 상상 최생+상(힘민지 최저)"
        ]
        msg = "📢 현재 딜러 악세 알림!\n"
        for deal_search, acc_name in zip(deal_search_list, deal_acc_name_list):
            # 1. API 호출 (이제 딕셔너리 혹은 None을 반환함)
            item_info = await search_lostark_auction(*deal_search)
            
            # 2. 결과 처리
            if item_info:
                name = item_info['name']
                price = item_info['price']
                
                # DB 저장 (수동으로 정한 acc_name과 API에서 가져온 price 저장)
                self.db.insert_price(acc_name, price)
                
                # 메시지 추가
                if price > 0:
                    msg += f"✅ {acc_name}: {price}G\n"
                else:
                    msg += f"❌ {acc_name}: 매물 없음\n"
                    
            else:
                # API 오류 등 None이 반환된 경우
                msg += f"⚠️ {acc_name}: 데이터 호출 실패\n"

        msg += "📢 현재 서폿 악세 알림!\n"
        for heal_search, acc_name in zip(heal_search_list, heal_acc_name_list):
            # 1. API 호출 (이제 딕셔너리 혹은 None을 반환함)
            item_info = await search_lostark_auction(*heal_search)
            
            # 2. 결과 처리
            if item_info:
                name = item_info['name']
                price = item_info['price']
                
                # DB 저장 (수동으로 정한 acc_name과 API에서 가져온 price 저장)
                self.db.insert_price(acc_name, price)
                
                # 메시지 추가
                if price > 0:
                    msg += f"✅ {acc_name}: {price}G\n"
                else:
                    msg += f"❌ {acc_name}: 매물 없음\n"
                    
            else:
                # API 오류 등 None이 반환된 경우
                msg += f"⚠️ {acc_name}: 데이터 호출 실패\n"
        
        for guild in self.bot.guilds:
            target_channel = discord.utils.get(guild.text_channels, name="알림") #서버의 채널 이름에 "알림"이 포함되어있어야 한다.
            print(msg)
            if target_channel:
                try:
                    await target_channel.send(msg) #목표 채널에 메시지를 전송
                except Exception as e:
                    print(f"{guild.name}에 메시지를 보내지 못했습니다: {e}")

async def setup(bot):
    await bot.add_cog(AuctionCog(bot))