import requests
import json

def search_lostark_auction():
    url = "https://developer-lostark.game.onstove.com/auctions/items"
    
    # 발급받으신 Bearer 토큰을 그대로 사용합니다.
    # 주의: 토큰은 만료될 수 있으니 주기적으로 확인이 필요합니다.
    headers = {
        'accept': 'application/json',
        'authorization': 'bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyIsImtpZCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyJ9.eyJpc3MiOiJodHRwczovL2x1ZHkuZ2FtZS5vbnN0b3ZlLmNvbSIsImF1ZCI6Imh0dHBzOi8vbHVkeS5nYW1lLm9uc3RvdmUuY29tL3Jlc291cmNlcyIsImNsaWVudF9pZCI6IjEwMDAwMDAwMDAxMzkzMzIifQ.TdpiHcqvp49-SNDO0MzxpKsCTLTC9BakNu3YPxS_4qw7851NEQV2rzVsGVJUuksvFFOXVttyB97VB6Gavj5jLaZiMRd1_dC5RhJzmx6bV6nNkn3lO2Q1aX1yCnTfPjPXuwaN5GZqyI3oYim5gPdb9tNQ8AicFVVG1FXg6VBd0GKpiZG7D1POIOAviTCOy-ahB6aZv7ZujeU5lDFHroLvvnfezHclqHijmvwijfHPs_GbAisJkMZOAqtdSXQ6Dnuz4ImyN4QLDmCPBKr7_fY79XOhJGHZS9Er0BquB1ul9iBF_PkXI3k-h6IW56w9NzVRSaB19Qdtys9BkYsz_Lty4g',
        'Content-Type': 'application/json'
    }

    # curl에서 전달된 데이터를 파이썬 딕셔너리로 변환
    payload = {
        "ItemLevelMin": 0,
        "ItemLevelMax": 0,
        "ItemGradeQuality": 70,
        "ItemUpgradeLevel": None,
        "ItemTradeAllowCount": None,
        "SkillOptions": [
            {
                "FirstOption": None,
                "SecondOption": None,
                "MinValue": None,
                "MaxValue": None
            }
        ],
        "EtcOptions": [
            { #힘민지
                "FirstOption": 1,
                "SecondOption": 11,
                "MinValue": 16000,
                "MaxValue": None
            },
            { #낙인상
                "FirstOption": 7,
                "SecondOption": 44,
                "MinValue": 800,
                "MaxValue": 800
            },
            { #아덴중
                "FirstOption": 7,
                "SecondOption": 43,
                "MinValue": 360,
                "MaxValue": 360
            }
        ],
        "Sort": "BIDSTART_PRICE",
        "CategoryCode": 200010,
        "CharacterClass": "바드",
        "ItemTier": 4,
        "ItemGrade": "고대",
        "ItemName": None,  # "string" 대신 None을 넣어야 전체 검색이 됩니다.
        "PageNo": 1,        # API는 보통 1페이지부터 시작합니다.
        "SortCondition": "ASC"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # 응답 확인
        if response.status_code == 200:
            result = response.json()
            items = result.get('Items', [])
            
            if not items:
                print("검색된 아이템이 없습니다.")
                return

            for item in items:
                name = item.get('Name')
                qly = item.get('GradeQuality')
                auction_info = item.get('AuctionInfo', {})
                buy_price = auction_info.get('BuyPrice')
                
                print(f"[{qly}] {name} | 즉시구매가: {buy_price}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"요청 중 오류 발생: {e}")

if __name__ == "__main__":
    search_lostark_auction()