import discord
from discord.ext import commands
import asyncio
from config import TOKEN # bot 인스턴스는 여기서 만들지 않고 app.py에서 직접 생성하는 게 좋습니다.

# 1. 봇 인스턴스 설정
intents = discord.Intents.default()
intents.message_content = True  # 필수!
bot = commands.Bot(command_prefix='!', intents=intents)

# 2. Cog 로드 함수
async def load_extensions():
    # cogs 폴더 안에 있는 goldbot.py와 auction.py를 불러옵니다.
    # 파일명이 cogs/goldbot.py, cogs/auction.py 라고 가정합니다.
    extensions = ['cogs.goldbot', 'cogs.auction']
    for ext in extensions:
        await bot.load_extension(ext)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # 이제 task 시작은 각 Cog의 __init__에서 처리하므로 여기서 호출할 필요가 없습니다.

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())