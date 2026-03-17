import sqlite3
from datetime import datetime

class AuctionDB:
    def __init__(self, db_path="lostark_auction.db"):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # id: 자동생성 번호
            # item_option: 직접 넣을 옵션 명칭 (예: '원한3 예둔3 치명')
            # buy_price: API에서 가져온 즉시구매가
            # created_at: 저장된 시간
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auction_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_option TEXT,
                    buy_price INTEGER,
                    created_at DATETIME
                )
            ''')
            conn.commit()

    def insert_price(self, option_name, buy_price):
        """
        직접 작성한 옵션명과 가격을 저장합니다.
        가격이 없거나(None) 0인 경우에도 0으로 기록합니다.
        """
        # 가격이 없으면(None) 0으로 변환, 있으면 그대로 사용
        save_price = buy_price if buy_price is not None else 0
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO auction_items (item_option, buy_price, created_at)
                VALUES (?, ?, ?)
            ''', (option_name, save_price, now))
            conn.commit()

    def get_last_price(self, option_name):
        """실제 가격 데이터(0보다 큰 값) 중 가장 최근 기록을 가져옵니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # WHERE 절에 buy_price > 0 조건을 추가합니다.
            cursor.execute('''
                SELECT buy_price FROM auction_items 
                WHERE item_option = ? AND buy_price > 0
                ORDER BY created_at DESC LIMIT 1
            ''', (option_name,))
            
            result = cursor.fetchone()
            
            # 결과가 있으면 가격(int) 반환, 없으면 None 반환
            return result[0] if result else None