import discord
import requests
import asyncio
from discord.ext import tasks, commands
from datetime import datetime, timedelta
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

    async def broadcast_embed(self, embed, chname="알림"):
        #모든 서버의 특정 이름을 가진 채널로 임베드 전송
        tasks = []
        for guild in self.bot.guilds:
            target_channel = discord.utils.get(guild.text_channels, name=chname)
            if target_channel:
                # 개별 전송을 코루틴으로 생성
                tasks.append(self._safe_send(target_channel, embed))
        
        if tasks:
            # 동시에 전송 시작
            await asyncio.gather(*tasks)

    async def _safe_send(self, channel, embed):
        """권한 체크를 포함한 안전한 전송"""
        # 봇에게 '메시지 보내기'와 '임베드 링크' 권한이 있는지 확인
        perms = channel.permissions_for(channel.guild.me)
        if not (perms.send_messages and perms.embed_links):
            return

        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"[{channel.guild.name}] 전송 실패: {e}")
                    
    @tasks.loop(time=ten_thirty_time)
    async def check_islands(self):
        islands = self.get_calenders(categoryName="모험 섬")
        
        if not islands:
            embed = discord.Embed(
                title="🏝️ 모험 섬 출현 알림",
                description="금일 예정된 골드 섬이 존재하지 않습니다. 😢",
                color=discord.Color.red()
            )
            await self.broadcast_embed(embed) # 중복 코드 한 줄로 해결
            return

        for entry in islands:
            try:
                name, time_str = entry.split(" - ")
                event_time = datetime.fromisoformat(time_str).replace(tzinfo=kst)
                alert_time = event_time - timedelta(minutes=10)
                
                now = datetime.now(kst)
                delay = (alert_time - now).total_seconds()

                if delay > 0:
                    self.bot.loop.create_task(self.scheduled_island_alert(delay, name, event_time))
            except Exception as e:
                print(f"파싱 에러: {e}")


    async def scheduled_island_alert(self, delay, island_name, event_time):
        await asyncio.sleep(delay)
        
        embed = discord.Embed(
            title="🏝️ 모험 섬 출현 알림",
            description=f"잠시 후 **{island_name}**이(가) 시작됩니다!",
            color=discord.Color.gold()
        )
        embed.add_field(name="시작 시간", value=f"🕒 {event_time.strftime('%H:%M')}", inline=False)
        embed.set_footer(text="골드 보상이 포함된 섬입니다.")

        await self.broadcast_embed(embed) # 중복 코드 한 줄로 해결

    @check_islands.before_loop
    async def before_check(self):
        # 1. 봇이 완전히 연결될 때까지 대기
        await self.bot.wait_until_ready()
        # 2. 봇이 켜진 직후, 오늘 남은 일정을 즉시 체크하여 예약
        print("봇 재시작 감지: 현재 시간 기준으로 일정을 즉시 체크합니다.")
        await self.check_islands()

    
    @commands.command(name="골드섬")
    async def check_gold_islands_now(self, ctx):
        #현재 시각을 기준으로 골드섬 정보를 즉시 출력합니다.
        islands = self.get_calenders(categoryName="모험 섬")
        
        if islands:
            msg = "📢 **현재 확인 가능한 골드섬 정보입니다:**\n" + "\n".join(islands)
            await ctx.send(msg)
        else:
            await ctx.send("현재 확인 가능한 골드섬이 없습니다. 😢")

    @tasks.loop(time=voyage_times) # 매일 지정된 시간(19, 21, 23시 10분 등)에 동작
    async def check_voyage_times(self):
        voyage_data = self.get_calenders(categoryName="항해")
        
        if not voyage_data:
            # 일정이 없을 경우의 임베드
            embed = discord.Embed(
                title="⚓ 항해 협동 알림",
                description="오늘 예정된 항해 일정이 없습니다. 🌊",
                color=discord.Color.red()
            )
        else:
            # 일정이 있을 경우의 임베드
            embed = discord.Embed(
                title="⚓ 항해 협동 알림",
                description="잠시 후 항해 협동 퀘스트가 시작됩니다!",
                color=discord.Color.blue()
            )
            # 리스트 내용을 예쁘게 합쳐서 필드에 추가
            voyage_list = "\n".join(voyage_data)
            embed.add_field(name="오늘의 항해 일정", value=f"```\n{voyage_list}\n```", inline=False)
            embed.set_footer(text="출항 준비를 서두르세요!")

        # 공용 함수를 사용하여 '항해' 채널로 전송
        await self.broadcast_embed(embed, chname="항해")

    @check_voyage_times.before_loop
    async def before_voyage_check(self):
        await self.bot.wait_until_ready()

# app.py에서 이 파일을 로드하기 위한 설정
async def setup(bot):
    await bot.add_cog(CalendarCog(bot))