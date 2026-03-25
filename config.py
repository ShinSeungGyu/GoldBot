import os
from dotenv import load_dotenv
from datetime import timezone, timedelta, time

load_dotenv()

# 설정
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = f"Bearer {os.getenv('LOSTARK_API_KEY')}"
kst = timezone(timedelta(hours=9))
notification_time = time(hour=10, minute=30, tzinfo=kst)