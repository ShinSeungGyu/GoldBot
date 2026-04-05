import discord
from discord.ext import commands
import asyncio
from config import TOKEN # bot 인스턴스는 여기서 만들지 않고 app.py에서 직접 생성하는 게 좋습니다.

# 1. 봇 인스턴스 설정
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 2. Cog 로드 함수
async def load_extensions():
    # cogs 폴더 안에 있는 goldbot.py와 auction.py를 불러옵니다.
    # 파일명이 cogs/calendar.py, cogs/auction.py 라고 가정합니다.
    extensions = ['cogs.calendar', 'cogs.auction']
    for ext in extensions:
        await bot.load_extension(ext)

@bot.event
async def on_guild_join(guild):
    category_name = "로스트아크"
    
    # 1. 카테고리 생성 (기본적으로 모두가 볼 수 있게)
    category = discord.utils.get(guild.categories, name=category_name)
    if not category:
        category = await guild.create_category(category_name)

    # 2. 채널별 설정 정의
    # (채널명, 채팅가능여부) 순서입니다.
    channels_to_create = [
        ("로아-악세", True),  # 채팅 가능
        ("로아-골드섬", False),   # 채팅 불가능 (읽기 전용)
        ("로아-항해", False)    # 채팅 불가능 (읽기 전용)
    ]

    for name, can_talk in channels_to_create:
        existing_channel = discord.utils.get(category.text_channels, name=name)
        if not existing_channel:
            # 💡 핵심: None 대신 빈 딕셔너리 {}로 시작합니다.
            overwrites = {} 
            
            if not can_talk:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=False
                    ),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True, 
                        send_messages=True
                    )
                }
                
            try:
                print(f"'{name}' 채널 생성 시도 중...")
                # 이제 overwrites가 {} 이므로 에러 없이 통과됩니다.
                await guild.create_text_channel(name, category=category, overwrites=overwrites)
                print(f"'{name}' 생성 성공!")
            except Exception as e:
                print(f"❌ '{name}' 생성 중 에러 발생: {e}")

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