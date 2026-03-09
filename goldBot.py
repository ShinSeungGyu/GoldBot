import discord
import os
import requests
from discord.ext import tasks, commands
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 설정
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = f"Bearer {os.getenv('LOSTARK_API_KEY')}"
CHANNEL_ID = 1234567890  # 알림을 보낼 채널 ID

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

def get_gold_islands():
    url = "https://developer-lostark.game.kr/contents/calendar"
    headers = {'accept': 'application/json', 'authorization': API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        gold_islands = []
        # API 응답 데이터 중 오늘 날짜의 '모험 섬' 중 보상에 '골드'가 포함된 항목 필터링
        # (실제 API 구조에 맞춘 파싱 로직 필요)
        return gold_islands
    return None

@tasks.loop(hours=1) # 혹은 지정된 시간대에 체크하도록 설정
async def check_islands():
    now = datetime.now()
    # 요청하신 시간: 9, 11, 13, 19, 21, 23시
    if now.hour in [9, 11, 13, 19, 21, 23]:
        islands = get_gold_islands()
        channel = bot.get_channel(CHANNEL_ID)
        if islands:
            msg = f"📢 **오늘의 골드섬 알림!**\n" + "\n".join(islands)
            await channel.send(msg)
        else:
            await channel.send("오늘은 골드섬이 없거나 확인되지 않습니다. 😢")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if not check_islands.is_running():
        check_islands.start()

bot.run(TOKEN)