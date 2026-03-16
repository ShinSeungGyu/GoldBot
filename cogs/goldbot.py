import discord
import requests
from discord.ext import tasks, commands
from datetime import datetime
from config import notification_time, API_KEY, kst

class GoldIslandCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cog가 로드될 때 루프를 자동으로 시작합니다.
        self.check_islands.start()

    def cog_unload(self):
        # Cog가 내려갈 때 루프를 종료합니다.
        self.check_islands.cancel()

    def get_gold_islands(self):
        url = 'https://developer-lostark.game.onstove.com/gamecontents/calendar'
        headers = {'accept': 'application/json', 'authorization': API_KEY}
        
        try:
            response = requests.get(url, headers=headers)
            now = datetime.now(kst).strftime("%Y-%m-%d")
            
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
                                    dates = item.get("StartTimes")
                                    if dates and isinstance(dates, list): 
                                        for date in dates:
                                            if date and date.startswith(now):
                                                gold_islands.append(f"{i['ContentsName']} - {date}")
                return gold_islands
        except Exception as e:
            print(f"API 요청 중 오류 발생: {e}")
        return None

    @tasks.loop(time=notification_time)
    async def check_islands(self):
        """매일 지정된 시간에 골드섬 알림 전송"""
        islands = self.get_gold_islands()
        
        if not islands:
            msg = "📢 금일 골드섬은 없습니다."
        else:
            msg = "📢 오늘의 골드섬 알림!\n" + "\n".join(islands)

        for guild in self.bot.guilds:
            target_channel = discord.utils.get(guild.text_channels, name="알림")
            if target_channel:
                try:
                    await target_channel.send(msg)
                except Exception as e:
                    print(f"{guild.name} 전송 실패: {e}")

    @commands.command(name="쌀섬")
    async def check_gold_islands_now(self, ctx):
        """현재 시각을 기준으로 골드섬 정보를 즉시 출력합니다."""
        islands = self.get_gold_islands()
        
        if islands:
            msg = "📢 **현재 확인 가능한 골드섬 정보입니다:**\n" + "\n".join(islands)
            await ctx.send(msg)
        else:
            await ctx.send("현재 확인 가능한 골드섬이 없습니다. 😢")

# app.py에서 이 파일을 로드하기 위한 설정
async def setup(bot):
    await bot.add_cog(GoldIslandCog(bot))