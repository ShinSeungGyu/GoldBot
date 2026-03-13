import discord
import os
import requests
import json
from discord.ext import tasks, commands
from datetime import time, timezone, timedelta, datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 설정
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = f"Bearer {os.getenv('LOSTARK_API_KEY')}"

intents = discord.Intents.default()
intents.message_content = True  # 필수!
bot = commands.Bot(command_prefix='!', intents=intents)

def get_gold_islands(): #골드 섬 정보 가져오기
    url = 'https://developer-lostark.game.onstove.com/gamecontents/calendar'
    headers = {'accept': 'application/json', 'authorization': API_KEY}
    response = requests.get(url, headers=headers)
    now = datetime.now().strftime("%Y-%m-%d") #2026-03-10
    
    if response.status_code == 200:
        gold_islands = []
        data = response.json()
        for i in data:
            if i.get("CategoryName") == "모험 섬":
                rewardItems = i.get("RewardItems", [])
                for r in rewardItems:
                    itemList = r.get("Items", [])
                    for item in itemList:
                        if item.get("Name") == "골드":
                            # 여기서 dates를 가져옵니다.
                            dates = item.get("StartTimes")
                            
                            # 바로 여기 안에서 체크해야 각 아이템의 날짜를 정확히 검사합니다!
                            if dates is not None and isinstance(dates, list): 
                                for date in dates:
                                    if date is not None and date.startswith(now):
                                        gold_islands.append(f"{i['ContentsName']} - {date}")
        return gold_islands
    return None


KST = timezone(timedelta(hours=9))
notification_time = time(hour=10, minute=30, tzinfo=KST)
# 한국 시간 10시 30분에 맞춰 설정
@tasks.loop(time=notification_time) #매일 10시 30분마다 각 서버의 알림채널에 메시지 전송
async def check_islands():
    # 골드섬 정보 가져오기
    islands = get_gold_islands()
    
    if not islands:
        msg = "📢 금일 골드섬은 없습니다."
    else:
        msg = f"📢 오늘의 골드섬 알림!\n" + "\n".join(islands)

    # 2. 봇이 속한 모든 서버(guild) 순회
    for guild in bot.guilds:
        target_channel = discord.utils.get(guild.text_channels, name="알림") #서버의 채널 이름에 "알림"이 포함되어있어야 한다.
        
        if target_channel:
            try:
                await target_channel.send(msg) #목표 채널에 메시지를 전송
            except Exception as e:
                print(f"{guild.name}에 메시지를 보내지 못했습니다: {e}")


@bot.command(name="쌀섬") #commands.Bot을 따라서 설정 - 이 경우 !쌀섬 으로 커멘드 생성
async def check_gold_islands_now(ctx):
    """현재 시각을 기준으로 골드섬 정보를 즉시 출력합니다."""
    # 1. API에서 전체 데이터를 가져옴 (기존 함수 재사용)
    islands = get_gold_islands()
    
    # 2. 메시지 생성
    if islands:
        # 데이터가 있으면 리스트를 줄바꿈해서 출력
        msg = f"📢 **현재 확인 가능한 골드섬 정보입니다:**\n" + "\n".join(islands)
        await ctx.send(msg)
    else:
        # 데이터가 없거나, 현재 시각에 해당되는 섬이 없을 때
        await ctx.send("현재 확인 가능한 골드섬이 없습니다. 😢")

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
    msg =f"📢 현재 딜러 악세 알림!\n"
    deal_search_list = [
        [200010, 17000, 41, 160, 42, 200],  #목걸이 중상
        [200010, 17000, 41, 260, 42, 120],  #목걸이 상중
        [200010, 17000, 41, 260, 42, 200],  #목걸이 상상
        [200020, 13000, 45, 95, 46, 300],   #귀걸이 중상
        [200020, 13000, 45, 155, 46, 180],  #귀걸이 상중
        [200020, 13000, 45, 155, 46, 300],  #귀걸이 상상
        [200030, 12000, 49, 95, 50, 400],   #반지 중상
        [200030, 12000, 49, 155, 50, 240],  #반지 상중
        [200030, 12000, 49, 155, 50, 400]   #반지 상상
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
    

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if not check_islands.is_running():
        check_islands.start()
    if not auction_acc.is_running():
        auction_acc.start()

@bot.event
async def on_message(message):
    # 1. 봇이 보낸 메시지인지 확인 (중요! 무한 루프 방지)
    if message.author == bot.user:
        return
    # 2. 이 줄이 있어야 bot.command로 만든 명령어들이 정상 작동합니다.
    await bot.process_commands(message)


bot.run(TOKEN) #봇 가동