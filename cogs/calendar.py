import discord
import requests
from discord.ext import tasks, commands
from datetime import datetime
from config import API_KEY, kst, ten_thirty_time, voyage_times


class CalendarCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cog가 로드될 때 루프를 자동으로 시작합니다.
        self.check_islands.start()
        self.check_voyage_times.start()

    def cog_unload(self):
        # Cog가 내려갈 때 루프를 종료합니다.
        self.check_islands.cancel()
        self.check_voyage_times.cancel()

    #로스트아크 API - 캘린더
    #categoryName: 모험 섬, 항해
    def get_calenders(self, categoryName):
        # API 설정 및 시간 초기화
        url = 'https://developer-lostark.game.onstove.com/gamecontents/calendar'
        headers = {'accept': 'application/json', 'authorization': API_KEY}
        
        # 입력값 정규화 (앞뒤 공백 제거)
        target_category = categoryName.strip()
        
        # 현재 시각 기준 설정 (비교를 위해 ISO 형식 유지)
        now_full = datetime.now(kst).strftime("%Y-%m-%dT%H")
        today_date = datetime.now(kst).strftime("%Y-%m-%d")

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return None

            data = response.json()
            results = []

            for item in data:
                # 1. 카테고리 일치 확인
                if item.get("CategoryName") != target_category:
                    continue
                # 2. '모험 섬'인 경우에만 '골드' 보상 여부 추가 체크
                if target_category == "모험 섬":
                    has_gold = False
                    # RewardItems -> Items 내에 '골드'가 있는지 확인
                    for reward in item.get("RewardItems", []):
                        
                        for r_item in reward.get("Items", []):
                            if r_item.get("Name") == "골드":
                                start_times = r_item.get("StartTimes", [])
                                has_gold = True
                                break
                        if has_gold: 
                            break

                    if not has_gold:
                        continue  # 골드 섬이 아니면 패스
                else:
                    start_times = item.get("StartTimes", [])
                
                # 3. 시간 필터링 (오늘 날짜 + 현재 시각 이후)
                if item.get("CategoryName") == "모험 섬":
                    day = today_date
                else:
                    day = now_full

                if isinstance(start_times, list):
                    for stime in start_times:
                        # 오늘 날짜로 시작하고, 현재 시각보다 크거나 같으면 추가
                        if stime and stime.startswith(day):
                            results.append(f"{item.get('ContentsName')} - {stime}")

            # 시간순 정렬 후 반환
            results.sort()
            return results
        except Exception as e:
            print(f"오류 발생: {e}")
            return None

    @tasks.loop(time=ten_thirty_time) #매일 10시 30분
    async def check_islands(self):
        #매일 지정된 시간에 골드섬 알림 전송
        islands = self.get_calenders(categoryName="모험 섬")
        
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

    @commands.command(name="골드섬")
    async def check_gold_islands_now(self, ctx):
        #현재 시각을 기준으로 골드섬 정보를 즉시 출력합니다.
        islands = self.get_calenders(categoryName="모험 섬")
        
        if islands:
            msg = "📢 **현재 확인 가능한 골드섬 정보입니다:**\n" + "\n".join(islands)
            await ctx.send(msg)
        else:
            await ctx.send("현재 확인 가능한 골드섬이 없습니다. 😢 테스트")

    @tasks.loop(time=voyage_times) #매일 19/21/23시 10분 마다 동작
    async def check_voyage_times(self):
        voyage_times = self.get_calenders(categoryName="항해")
        if not voyage_times:
            msg = "📢 금일 항해 일정은 없습니다."
        else:
            msg = "📢 항해 협동 알림!\n" + "\n".join(voyage_times)

        for guild in self.bot.guilds:
            target_channel = discord.utils.get(guild.text_channels, name="항해")
            if target_channel:
                try:
                    await target_channel.send(msg)
                except Exception as e:
                    print(f"{guild.name} 전송 실패: {e}")

# app.py에서 이 파일을 로드하기 위한 설정
async def setup(bot):
    await bot.add_cog(CalendarCog(bot))