import os
import discord
from discord.ext import commands
from datetime import timezone, timedelta, time

# 설정
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = f"Bearer {os.getenv('LOSTARK_API_KEY')}"
kst = timezone(timedelta(hours=9))
notification_time = time(hour=8, minute=30, tzinfo=kst)