import requests
import json

def get_auction_options():
    # 1. API 엔드포인트 설정
    url = "https://developer-lostark.game.onstove.com/auctions/options"
    
    # 2. 헤더 설정 (본인의 API Key를 입력하세요)
    # 'bearer ' 다음에 오는 토큰 문자열을 그대로 유지해야 합니다.
    headers = {
        'accept': 'application/json',
        'authorization': 'bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyIsImtpZCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyJ9.eyJpc3MiOiJodHRwczovL2x1ZHkuZ2FtZS5vbnN0b3ZlLmNvbSIsImF1ZCI6Imh0dHBzOi8vbHVkeS5nYW1lLm9uc3RvdmUuY29tL3Jlc291cmNlcyIsImNsaWVudF9pZCI6IjEwMDAwMDAwMDAxMzkzMzIifQ.TdpiHcqvp49-SNDO0MzxpKsCTLTC9BakNu3YPxS_4qw7851NEQV2rzVsGVJUuksvFFOXVttyB97VB6Gavj5jLaZiMRd1_dC5RhJzmx6bV6nNkn3lO2Q1aX1yCnTfPjPXuwaN5GZqyI3oYim5gPdb9tNQ8AicFVVG1FXg6VBd0GKpiZG7D1POIOAviTCOy-ahB6aZv7ZujeU5lDFHroLvvnfezHclqHijmvwijfHPs_GbAisJkMZOAqtdSXQ6Dnuz4ImyN4QLDmCPBKr7_fY79XOhJGHZS9Er0BquB1ul9iBF_PkXI3k-h6IW56w9NzVRSaB19Qdtys9BkYsz_Lty4g',
        'Content-Type': 'application/json'
    }

    try:
        # 3. GET 요청 보내기
        response = requests.get(url, headers=headers)

        # 4. 응답 확인
        if response.status_code == 200:
            options_data = response.json()
            
            # 데이터가 매우 방대하므로 파일로 저장하거나 일부만 출력하는 것이 좋습니다.
            with open("lostark_options.json", "w", encoding="utf-8") as f:
                json.dump(options_data, f, ensure_ascii=False, indent=4)
            
            print("성공! 모든 옵션 정보를 'lostark_options.json' 파일로 저장했습니다.")
            
            # 구조 확인을 위해 상위 키(Key)들만 출력해봅니다.
            print(f"가져온 정보 카테고리: {list(options_data.keys())}")
            
        else:
            print(f"오류 발생: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"요청 중 문제가 발생했습니다: {e}")

if __name__ == "__main__":
    get_auction_options()