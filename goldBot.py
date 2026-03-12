import discord
import os
import requests
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


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if not check_islands.is_running():
        check_islands.start()

@bot.event
async def on_message(message):
    # 1. 봇이 보낸 메시지인지 확인 (중요! 무한 루프 방지)
    if message.author == bot.user:
        return
    # 2. 이 줄이 있어야 bot.command로 만든 명령어들이 정상 작동합니다.
    await bot.process_commands(message)


bot.run(TOKEN) #봇 가동