import os
from dotenv import load_dotenv
from datetime import timezone, timedelta, time

load_dotenv()

# 설정
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = f"Bearer {os.getenv('LOSTARK_API_KEY')}"

kst = timezone(timedelta(hours=9))
ten_thirty_time = time(hour=10, minute=30, tzinfo=kst)
voyage_times = [
    time(hour=19, minute=15, tzinfo=kst), 
    time(hour=21, minute=15, tzinfo=kst), 
    time(hour=23, minute=15, tzinfo=kst)
    ]