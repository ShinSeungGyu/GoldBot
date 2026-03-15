import os
import discord
from goldbot import check_islands
from auction import auction_acc
from discord.ext import commands
from datetime import timezone, timedelta, time


# 설정
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = f"Bearer {os.getenv('LOSTARK_API_KEY')}"

intents = discord.Intents.default()
intents.message_content = True  # 필수!
bot = commands.Bot(command_prefix='!', intents=intents)
kst = timezone(timedelta(hours=9))
notification_time = time(hour=10, minute=30, tzinfo=kst)
    
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