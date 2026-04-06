import discord
from discord.ext import commands
import asyncio
from config import TOKEN

# 1. 봇 인스턴스 설정

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.message_content = True # 하이브리드 커맨드나 메시지 읽기 권한이 필요하다면
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        extensions = ['cogs.auction', 'cogs.calendar']
        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ {ext} 로드 성공")
            except Exception as e:
                print(f"❌ {ext} 로드 실패: {e}")
        
        await self.tree.sync()
        print("✅ 슬래시 명령어 동기화 완료!")

    async def on_guild_join(self, guild):
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

    async def on_ready(self):
        print(f'Logged in as {bot.user.name}')


bot = MyBot()
bot.run(TOKEN)