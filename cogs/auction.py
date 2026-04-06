import aiohttp
import discord
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import io
import os
from discord import ui
from database import AuctionDB
from datetime import time, datetime
from discord.ext import tasks, commands
from discord import app_commands
from config import API_KEY, kst



# 경매장 검색
# Acc에 따라 검색(목걸이, 귀걸이, 반지)
# 각 악세별 상상상 악세를 호출
# 악세별 힘민지가 다르므로 payload를 악세별로 작성해서 여러번 전송
async def search_lostark_auction(acc, base, option1, value1, option2, value2, option3, value3):
    url = "https://developer-lostark.game.onstove.com/auctions/items"
    headers = {'Content-Type': 'application/json','authorization': API_KEY, 'accept': 'application/json'}
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
            { #악세별 힘민지 최소값 (목걸이:17000, 귀걸이:13000, 반지:12000 )
                "FirstOption": 1,
                "SecondOption": 11,
                "MinValue": base,
                "MaxValue": None
            },
            # option > 추피:41, 적주피:42, 아덴획득량:43, 낙인력:44 | 공격력 %:45, 무기 공격력 %:46 | 치적:49, 치피:50, 아공강:51, 아피강:52, 
            { 
                "FirstOption": 7, 
                "SecondOption": option1,
                "MinValue": value1,
                "MaxValue": value1
            },
            # value > 추피:260, 적주피:200, 아덴획득량:600, 낙인력:800 | 공격력 %:155, 무기 공격력 %:300 | 치적:155, 치피:400, 아공강:500, 아피강:750
            {
                "FirstOption": 7, 
                "SecondOption": option2,
                "MinValue": value2,
                "MaxValue": value2
            },
            {   #딜러:공+(53/390) / 서폿:무공+(54/960), 최생+(55/6500)
                "FirstOption": 7, 
                "SecondOption": option3,
                "MinValue": value3,
                "MaxValue": value3
            }
        ],
        "Sort": "BIDSTART_PRICE",
        "CategoryCode": acc,        #악세별 코드값 ( 목걸이:200010, 귀걸이:200020, 반지:200030 )
        "CharacterClass": "바드",   #임의 직업 지정
        "ItemTier": 4,
        "ItemGrade": "고대",
        "ItemName": None,  # "string" 대신 None을 넣어야 전체 검색이 됩니다.
        "PageNo": 1,        # API는 보통 1페이지부터 시작합니다.
        "SortCondition": "ASC"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status_code == 200:
                    result = response.json()
                    items = result.get('Items', [])
                    
                    if not items:
                        print("검색된 아이템이 없습니다.")
                        # 매물이 없으므로 이름은 유지하되 가격은 0으로 반환하거나 None 반환
                        return {"name": "검색 결과 없음", "price": 0}
                    
                    # 첫 번째 아이템(최저가) 정보만 추출
                    item = items[0]
                    name = item.get('Name')
                    # BuyPrice가 없으면 0으로 설정
                    price = item.get('AuctionInfo', {}).get('BuyPrice', 0)
                    
                    # 리스트가 아닌 필요한 정보만 딱 담아서 반환
                    return {"name": name, "price": price}

                else:
                    print(f"Error: {response.status_code}")
                    return None

    except Exception as e:
        print(f"요청 중 오류 발생: {e}")
        return None


# 옵션명 -> API 코드값 (FirstOption: 7 고정, SecondOption: 아래 값)
OPTION_CODES = {
    "추가 피해": 41, "적에게 주는 피해": 42, "아덴 게이지 수급량": 43, "낙인력": 44,
    "공격력 %": 45, "무기 공격력 %": 46, "파티원 회복 효과": 47, "파티원 보호막 효과": 48,
    "치명타 적중률": 49, "치명타 피해": 50,
    "아군 공격력 강화": 51, "아군 피해량 강화": 52,
    "공격력": 53, "무기 공격력": 54, "최대 생명력": 55 # 마지막 단계 공통 옵션
}

# 표시 텍스트 -> 실제 정수 값
# 예: "1.04%" -> 104
VALUE_MAPS = {
    # 0.xx 단위
    "0.40%": 40, "0.55%": 55, "0.70%": 70, "0.80%": 80, "0.95%": 95,
    # 1.xx 단위
    "1.10%": 110, "1.20%": 120, "1.35%": 135, "1.55%": 155, "1.60%": 160, "1.80%": 180,
    # 2.xx 단위
    "2.00%": 200, "2.10%": 210, "2.15%": 215, "2.40%": 240, "2.60%": 260,
    # 3.xx 단위 이상
    "3.00%": 300, "3.50%": 350, "3.60%": 360, "4.00%": 400, "4.50%": 450, 
    "4.80%": 480, "5.00%": 500, "6.00%": 600, "7.50%": 750, "8.00%": 800,

    #공통 옵션
    "80": 80, "195": 195, "390": 390,
    "480": 480, "960": 960,
    "1300": 1300, "3250": 3250, "6500":6500
}

OPTION_VALUE_LISTS = {
    # 목걸이 옵션
    "추가 피해": ["0.70%", "1.60%", "2.60%"],
    "적에게 주는 피해": ["0.55%", "1.20%", "2.00%"],
    "아덴 게이지 수급량": ["1.60%", "3.60%", "6.00%"],
    "낙인력": ["2.15%", "4.80%", "8.00%"],

    # 귀걸이 옵션
    "공격력 %": ["0.40%", "0.95%", "1.55%"],
    "무기 공격력 %": ["0.80%", "1.80%", "3.00%"],
    "파티원 보호막 효과": ["0.95%", "2.10%", "3.50%"],
    "파티원 회복 효과": ["0.95%", "2.10%", "3.50%"],

    # 반지 옵션
    "치명타 적중률": ["0.40%", "0.95%", "1.55%"],
    "치명타 피해": ["1.10%", "2.40%", "4.00%"],
    "아군 공격력 강화": ["1.35%", "3.00%", "5.00%"],
    "아군 피해량 강화": ["2.00%", "4.50%", "7.50%"],

    #공통 옵션
    "공격력": ["80", "195", "390"],
    "무기 공격력": ["195", "480", "960"],
    "최대 생명력": ["1300", "3250", "6500"]
}

STAT_LIMITS = {
    200010: {"min": 15178, "max": 17857, "guide": "15178~17857"}, # 목걸이
    200020: {"min": 11806, "max": 13889, "guide": "11806~13889"}, # 귀걸이
    200030: {"min": 10962, "max": 12897, "guide": "10962~12897"}  # 반지
}

ACC_NAMES = {
    200010: "목걸이",
    200020: "귀걸이",
    200030: "반지"
}

ACC_DATA = {
    200010: {"딜러": ["추가 피해", "적에게 주는 피해"], "서폿": ["아덴 게이지 수급량", "낙인력"]},
    200020: {"딜러": ["공격력 %", "무기 공격력 %"], "서폿": ["무기 공격력 %", "파티원 보호막 효과", "파티원 회복 효과"]},
    200030: {"딜러": ["치명타 적중률", "치명타 피해"], "서폿": ["아군 공격력 강화", "아군 피해량 강화"]}
}

SUPPORT_EXTRA_OPTS = ["파티원 보호막 효과", "파티원 회복 효과", "무기 공격력", "최대 생명력"]

class StatModal(ui.Modal):
    def __init__(self, view, acc_id: int):
        acc_name = ACC_NAMES[acc_id]
        super().__init__(title=f"{acc_name} 스탯 입력")
        self.view = view
        self.acc_id = acc_id # 이미 int형
        
        limit_info = STAT_LIMITS[acc_id]
        self.power = ui.TextInput(
            label="힘/민/지 수치", 
            placeholder=f"범위: {limit_info['guide']}",
            min_length=1, max_length=6
        )
        self.add_item(self.power)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.power.value
        if not value.isdigit():
            return await interaction.response.send_message("❌ 숫자만 입력하세요.", ephemeral=True)
        
        num_value = int(value)
        # self.acc_id가 int형인지 다시 한 번 확인하세요.
        limit = STAT_LIMITS.get(int(self.acc_id)) 

        if not limit or num_value < limit['min'] or num_value > limit['max']:
            return await interaction.response.send_message(
                f"❌ 범위를 벗어났습니다. ({limit['guide']})", 
                ephemeral=True
            )

        # 데이터 저장
        self.view.search_data['stat_value'] = num_value
        
        # ✅ 핵심: 여기서 바로 다음 메뉴를 '수정' 모드로 호출합니다.
        # 따로 함수를 호출하지 않고 show_position_menu 로직을 태우기 위해 interaction을 보냅니다.
        await self.view.show_position_menu(interaction)

# [AccessorySearchView: int 변환 로직 적용]
class AccessorySearchView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.search_data = {}

    @ui.select(placeholder="1. 장신구 종류 선택", options=[
        discord.SelectOption(label="반지", value=200030),
        discord.SelectOption(label="귀걸이", value=200020),
        discord.SelectOption(label="목걸이", value=200010)
    ])

    async def select_acc_type(self, interaction: discord.Interaction, select: ui.Select):
        # SelectOption의 value는 str이므로 int로 변환하여 저장
        selected_id = int(select.values[0])
        self.search_data['type_id'] = selected_id
        
        # int형 id를 그대로 모달에 전달
        await interaction.response.send_modal(StatModal(self, selected_id))

    async def show_position_menu(self, interaction: discord.Interaction):
        self.clear_items()
        btn_dealer = ui.Button(label="딜러 옵션", style=discord.ButtonStyle.danger, custom_id="dealer")
        btn_support = ui.Button(label="서폿 옵션", style=discord.ButtonStyle.primary, custom_id="support")

        async def position_callback(inter: discord.Interaction):
            # 1. 포지션 데이터 저장
            self.search_data['position'] = "딜러" if inter.data['custom_id'] == "dealer" else "서폿"
            
            # 2. 상호작용 실패를 방지하기 위해 다음 단계로 바로 넘깁니다.
            # (show_option_list 함수 내부에서 interaction.response.edit_message를 호출하게 됨)
            await self.show_option_list(inter)

        btn_dealer.callback = position_callback
        btn_support.callback = position_callback
        
        self.add_item(btn_dealer)
        self.add_item(btn_support)

        # 모달에서 넘어온 상호작용 응답 처리
        if not interaction.response.is_done():
            await interaction.response.edit_message(content="✅ 포지션을 선택해주세요.", view=self)
        else:
            await interaction.edit_original_response(content="✅ 포지션을 선택해주세요.", view=self)

    async def show_option_list(self, interaction: discord.Interaction):
        # 💡 버튼 클릭(상호작용)에 대한 즉각적인 응답
        # 만약 로직이 길어질 것 같으면 defer를 사용하세요.
        # 여기서는 바로 메시지를 수정하므로 edit_message를 사용합니다.
        
        self.clear_items()
        acc_id = self.search_data['type_id']
        pos = self.search_data['position']
        
        options_list = ACC_DATA[acc_id][pos]
        select_options = [discord.SelectOption(label=opt, value=opt) for opt in options_list]
        
        opt_select = ui.Select(placeholder=f"2. {ACC_NAMES[acc_id]} {pos} 옵션 선택", options=select_options)

        async def opt_callback(inter: discord.Interaction):
            self.search_data['main_opt_name'] = opt_select.values[0]
            self.search_data['main_opt_code'] = OPTION_CODES[opt_select.values[0]]
            await self.show_value_list(inter)

        opt_select.callback = opt_callback
        self.add_item(opt_select)

        # ✅ 여기서 응답을 완료합니다.
        await interaction.response.edit_message(content=f"✅ 포지션: **{pos}** 가 선택되었습니다.", view=self)

    async def show_value_list(self, interaction: discord.Interaction):
        self.clear_items()
        main_opt = self.search_data['main_opt_name']
        vals = OPTION_VALUE_LISTS.get(main_opt, [])
        val_options = [discord.SelectOption(label=v, value=v) for v in vals]
        
        val_select = ui.Select(placeholder=f"3. {main_opt} 수치 선택", options=val_options)

        async def val_callback(inter: discord.Interaction):
            # 중복 응답 방지를 위해 defer를 사용하거나 edit_message를 한 번만 사용
            if not inter.response.is_done():
                selected_text = val_select.values[0]
                self.search_data['value1'] = VALUE_MAPS[selected_text]
                await self.show_second_option_list(inter)

        val_select.callback = val_callback
        self.add_item(val_select)
        await interaction.response.edit_message(content=f"✅ 첫 번째 옵션 [{main_opt}]의 수치를 선택하세요.", view=self)

    async def show_second_option_list(self, interaction: discord.Interaction):
        self.clear_items()
        acc_id = self.search_data['type_id']
        pos = self.search_data['position']
        
        # 1. 첫 번째 단계에서 골랐던 옵션 이름 가져오기
        first_opt = self.search_data.get('main_opt_name')
        # 기본 옵션 리스트
        options_list = list(ACC_DATA[acc_id][pos])

        if pos == "서폿" and acc_id == 200020:
            for extra in ["무기 공격력", "최대 생명력"]:
                if extra not in options_list:
                    options_list.append(extra)

        # 중복 제거: 첫 번째 옵션이 리스트에 있다면 제외
        filtered_options = [opt for opt in options_list if opt != first_opt]
        
        select_options = [discord.SelectOption(label=opt, value=opt) for opt in filtered_options]
        second_opt_select = ui.Select(placeholder="4. 두 번째 옵션 선택", options=select_options)

        async def second_opt_callback(inter: discord.Interaction):
            name = second_opt_select.values[0]
            self.search_data['main_opt2_name'] = name
            self.search_data['option2_code'] = OPTION_CODES[name]
            await self.show_second_value_list(inter)

        second_opt_select.callback = second_opt_callback
        self.add_item(second_opt_select)
        await interaction.response.edit_message(content="✅ **두 번째 옵션**을 선택하세요.", view=self)

    async def show_second_value_list(self, interaction: discord.Interaction):

        self.clear_items()
        opt2_name = self.search_data['main_opt2_name']
        vals = OPTION_VALUE_LISTS.get(opt2_name, [])
        val_options = [discord.SelectOption(label=v, value=v) for v in vals]
        
        val_select = ui.Select(placeholder=f"5. {opt2_name} 수치 선택", options=val_options)

        async def val_callback(inter: discord.Interaction):
            selected_text = val_select.values[0]
            # 두 번째 옵션의 수치 저장
            self.search_data['value2'] = VALUE_MAPS[selected_text]
            
            # 이제 진짜 마지막(공통 옵션) 단계로 이동
            await self.show_final_step(inter)

        val_select.callback = val_callback
        self.add_item(val_select)
        await interaction.response.edit_message(content=f"✅ 두 번째 옵션 [{opt2_name}]의 수치를 선택하세요.", view=self)
    
    async def show_final_step(self, interaction: discord.Interaction):
        self.clear_items()
        acc_id = self.search_data['type_id']
        pos = self.search_data['position']
        
        picked = [self.search_data.get('main_opt_name'), self.search_data.get('main_opt2_name')]
        # 서폿은 3번 슬롯에서도 모든 유효 옵션을 선택할 수 있게 구성
        if pos == "서폿":
            if acc_id == 200020:
                options = ["파티원 보호막 효과", "파티원 회복 효과", "무기 공격력", "최대 생명력"]
            else:
                options = ["무기 공격력", "최대 생명력"]
        else:
            options = ["공격력", "무기 공격력", "최대 생명력"]

        final_options = [opt for opt in options if opt not in picked]
    
        final_type_select = ui.Select(placeholder="6. 마지막 세 번째 옵션 종류 선택", options=[discord.SelectOption(label=opt, value=opt) for opt in final_options])

        async def type_callback(inter: discord.Interaction):
            name = final_type_select.values[0]
            self.search_data['main_opt3_name'] = name
            self.search_data['option3_code'] = OPTION_CODES[name]
            # 수치 선택(상/중/하) 단계로 이동
            await self.show_final_value_list(inter)

        final_type_select.callback = type_callback
        self.add_item(final_type_select)
        await interaction.response.edit_message(content="✅ **마지막 세 번째 옵션**의 종류를 선택하세요.", view=self)

    async def show_final_value_list(self, interaction: discord.Interaction):
        self.clear_items()
        opt_name = self.search_data['main_opt3_name']
        
        # OPTION_VALUE_LISTS에서 "공격력" 식으로 가져옴
        vals = OPTION_VALUE_LISTS.get(opt_name, [])
        val_options = [discord.SelectOption(label=v, value=v) for v in vals]
        
        val_select = ui.Select(placeholder=f"7. {opt_name} 수치 선택", options=val_options)

        async def val_callback(inter: discord.Interaction):
            selected_text = val_select.values[0]
            self.search_data['option3_value'] = VALUE_MAPS[selected_text] # 숫자 저장
            
            # 최종 검색 버튼 등장
            search_btn = ui.Button(label="🔍 모든 조건으로 검색 시작", style=discord.ButtonStyle.success)
            
            async def search_click(i: discord.Interaction):
                d = self.search_data
                await i.response.defer(ephemeral=True)
                try:
                    auction_acc = await search_lostark_auction(
                        acc=d['type_id'], base=d['stat_value'],
                        option1=d['main_opt_code'], value1=d['value1'],
                        option2=d['option2_code'], value2=d['value2'],
                        option3=d['option3_code'], value3=d['option3_value']
                    )
                    embed = discord.Embed(
                        title="✅ 경매장 검색 완료!",
                        description=f"**{auction_acc['name']}**\n  힘민지 {d['stat_value']} 이상",
                        color=0xFFFFFF
                    )
                    # 2. 필드 추가 (inline=True로 설정하면 가로로 배치됩니다)
                    embed.add_field(name=d['main_opt_name'], value=f"{int(d['value1']) / 100:.2f}%", inline=True)
                    embed.add_field(name=d['main_opt2_name'], value=f"{int(d['value2']) / 100:.2f}%", inline=True)
                    embed.add_field(name=d['main_opt3_name'], value=f"{d['option3_value']}", inline=True)

                    # 3. 가격 정보 추가 (돋보이게 큰 필드로)
                    embed.add_field(name="💰 최저가 정보", value=f"**{auction_acc['price']:,} G**", inline=False)

                    # 4. 하단에 시간 정보 등 추가 가능
                    embed.set_footer(text="로스트아크 경매장 알림 서비스")

                    # 5. 전송 (content 대신 embed 인자를 사용합니다)
                    await i.followup.send(embed=embed, ephemeral=True)
                except Exception as e:
                    await i.followup.send(f"❌ 오류: {e}", ephemeral=True)

            search_btn.callback = search_click
            self.clear_items()
            self.add_item(val_select) # 선택 유지용
            self.add_item(search_btn)
            await inter.response.edit_message(content=f"✅ 모든 설정 완료! ({opt_name} {selected_text})", view=self)

        val_select.callback = val_callback
        self.add_item(val_select)
        await interaction.response.edit_message(content=f"✅ **{opt_name}**의 세부 수치를 선택하세요.", view=self)


class AuctionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 이렇게 하면 이 클래스 안의 모든 함수에서 self.db를 쓸 수 있습니다.
        self.db = AuctionDB("lostark_auction.db")
    
    @app_commands.command(name="악세검색", description="로스트아크 연마 장신구를 검색합니다.")
    async def acc_search(self, interaction: discord.Interaction):
        # 1. View 인스턴스 생성
        view = AccessorySearchView()
        
        # 2. ✅ ctx.send 대신 interaction.response.send_message 사용
        # 이 방식이어야만 ephemeral=True가 먹히고 '메시지 닫기' 버튼이 생깁니다.
        await interaction.response.send_message(
            content="🛡️ **로스트아크 경매장 맞춤 검색을 시작합니다.**\n장신구 부위를 먼저 선택해주세요!", 
            view=view, 
            ephemeral=True
        )

    async def build_price_line(self, search, acc_name):
        last_price = self.db.get_last_price(acc_name)
        item_info = await search_lostark_auction(*search)

        if item_info:
                price = item_info['price']
                self.db.insert_price(acc_name, price)
                
                if price is not None and price > 0:
                    if last_price is None or last_price == 0:
                        change_emoji = "✅" 
                        diff_text = ""
                    elif price > last_price:
                        # 가격 상승: 빨간 삼각형
                        change_emoji = "🔺"
                        # 계산 결과 뒤에 : , 를 붙여 콤마 추가
                        diff_text = f" (▲{price - last_price:,})" #{n:,} >> 천 단위 콤마 추가, {n:.2f} >> 소수점 둘째 자리까지 반올림, {n:,.0f} >> 콤마를 찍으면서 소수점 없앰
                    elif price < last_price:
                        # 가격 하락: 파란색 아래 화살표
                        change_emoji = "🔽" 
                        # 계산 결과 뒤에 : , 를 붙여 콤마 추가
                        diff_text = f" (▼{last_price - price:,})"
                    else:
                        change_emoji = "➖"
                        diff_text = ""
                    
                    # price 변수 뒤에 :, 를 붙여 콤마 추가
                    msg += f"{change_emoji} {acc_name}: {price:,}G{diff_text}\n"
                else:
                    msg += f"❌ {acc_name}: 매물 없음\n"
        return msg

    scheduled_times = [time(hour=h, minute=0, second=0) for h in range(24)]
    # time=scheduled_times / minutes=1
    @tasks.loop(time=scheduled_times)
    async def auction_acc(self):
        print("악세 검색 시작")
        deal_search_list = [
            [200010, 17000, 41, 260, 42, 200, 53, 390],  #목걸이 추피상 적주피상 공+상
            [200010, 15178, 41, 260, 42, 200, 53, 390],  #목걸이 추피상 적주피상 공+상 (최저가)
            #----------------------------------------------------------------------------------
            [200020, 13000, 45, 155, 46, 300, 53, 390],  #귀걸이 공%상 무공%상 공+상
            [200020, 11806, 45, 155, 46, 300, 53, 390],  #귀걸이 공%상 무공%상 공+상 (최저가)
            #----------------------------------------------------------------------------------
            [200030, 12000, 49, 155, 50, 400, 53, 390],   #반지 치적상 치피상 공+상
            [200030, 10962, 49, 155, 50, 400, 53, 390]   #반지 치적상 치피상 공+상 (최저가)
        ]
        deal_acc_name_list = [
            "딜러 목걸이 상상상",
            "딜러 목걸이 상상상(힘민지 최저)",
            "딜러 귀걸이 상상상",
            "딜러 귀걸이 상상상(힘민지 최저)",
            "딜러 반지 상상상",
            "딜러 반지 상상상(힘민지 최저)"
        ]
        heal_search_list = [
            [200010, 17000, 43, 600, 44, 800, 54, 960],     #목걸이 상상 무공+상
            [200010, 15178, 43, 600, 44, 800, 54, 960],     #목걸이 상상 무공+상 (최저가)
            [200010, 17000, 43, 600, 44, 800, 55, 6500],    #목걸이 상상 최생+상
            [200010, 15178, 43, 600, 44, 800, 55, 6500],    #목걸이 상상 최생+상 (최저가)
            #----------------------------------------------------------------------------------
            [200020, 13000, 46, 300, 54, 960, 55, 6500],    #귀걸이 공%상 무공+상 최생+상
            [200020, 11806, 46, 300, 54, 960, 55, 6500],    #귀걸이 공%상 무공+상 최생+상 (최저가)
            #----------------------------------------------------------------------------------
            [200030, 12000, 51, 500, 52, 750, 54, 960],     #반지 상상 무공+상
            [200030, 10962, 51, 500, 52, 750, 54, 960],     #반지 상상 무공+상 (최저가)
            [200030, 12000, 51, 500, 52, 750, 55, 6500],    #반지 상상 최생+상
            [200030, 10962, 51, 500, 52, 750, 55, 6500]    #반지 상상 최생+상 (최저가)
        ]
        heal_acc_name_list = [
            "서폿 목걸이 상상 무공+",
            "서폿 목걸이 상상 최생+(힘민지 최저)",
            "서폿 목걸이 상상 최생+",
            "서폿 목걸이 상상 최생+(힘민지 최저)",
            "서폿 귀걸이 상 무공+상 최생+상",
            "서폿 귀걸이 상 무공+상 최생+상(힘민지 최저)",
            "서폿 반지 상상 무공+상",
            "서폿 반지 상상 무공+상(힘민지 최저)",
            "서폿 반지 상상 최생+상",
            "서폿 반지 상상 최생+상(힘민지 최저)"
        ]
        msg = "📢 현재 딜러 악세 알림!\n"
        for s, name in zip(deal_search_list, deal_acc_name_list):
            msg += await self.build_price_line(s, name)
            
        msg += "\n📢 현재 서폿 악세 알림!\n"
        for s, name in zip(heal_search_list, heal_acc_name_list):
            msg += await self.build_price_line(s, name)
        
        print(msg)
        now_str = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')
        for guild in self.bot.guilds:
            # 서버에서 "로아-악세"라는 이름의 텍스트 채널 찾기
            target_channel = discord.utils.get(guild.text_channels, name="로아-악세")
            if target_channel:
                try:
                    # 1. 임베드 객체 생성
                    # title: 제목, description: 내용(여기에 msg가 들어감), color: 왼쪽 띠 색상
                    embed = discord.Embed(
                        title="💰 실시간 악세 최저가 알림",
                        description=msg, 
                        color=discord.Color.gold() # 골드색 (또는 .blue(), .green() 등 선택 가능)
                    )
                    
                    # (선택 사항) 하단에 업데이트 시간 표시
                    embed.set_footer(text=f"마지막 업데이트: {now_str} (KST)")

                    # 2. 임베드 전송 (content 대신 embed 인자를 사용합니다)
                    await target_channel.send(embed=embed)
                    
                except Exception as e:
                    print(f"{guild.name}에 메시지를 보내지 못했습니다: {e}")



    # DB값 가져와서 데이터프레임으로 변환하기
    def get_df_from_db(self, item_option=None):
        conn = sqlite3.connect(self.db.db_path)
        search_term = f"%{item_option}%"
        
        if item_option:
            query = "SELECT item_option, buy_price, created_at FROM auction_items WHERE item_option like ? ORDER BY created_at ASC"
            df = pd.read_sql_query(query, conn, params=(search_term,))
        else:
            query = "SELECT item_option, buy_price, created_at FROM auction_items ORDER BY created_at ASC"
            df = pd.read_sql_query(query, conn)
            
        conn.close()
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df

    # 데이터프레임으로 선그래프 이미지 생성
    def generate_graph(self, df, title_suffix=""):

        font_path = '/home/container/font/NanumGothic.ttf'
        
        # 폰트 설정 초기화
        fp = None
        if os.path.isfile(font_path):
            # 1. 폰트 파일 객체 생성 (이 객체를 직접 주입해야 함)
            fp = fm.FontProperties(fname=font_path)
            print(f"✅ 폰트 로드 성공: {fp.get_name()}")
        else:
            print(f"❌ 폰트 파일을 찾을 수 없습니다: {font_path}")

        plt.figure(figsize=(12, 6)) # 범례 공간을 위해 가로를 조금 더 넓혔습니다.
        
        # 옵션별 그룹핑 시각화
        for option, group in df.groupby('item_option'):
            # 레이블(label)에 한글이 들어갈 수 있으므로 범례 설정 시 중요함
            plt.plot(group['created_at'], group['buy_price'], marker='o', label=option)

        # 2. 모든 텍스트 요소에 fontproperties=fp 적용
        if fp:
            plt.title(f'로스트아크 악세 시세 변동 {title_suffix}', fontproperties=fp, fontsize=16)
            plt.xlabel('시간', fontproperties=fp)
            plt.ylabel('구매 가격 (Gold)', fontproperties=fp)
            
            # 축 눈금(Ticks) 한글 깨짐 방지
            plt.xticks(rotation=45, fontproperties=fp)
            plt.yticks(fontproperties=fp)
            
            # 범례(Legend) 한글 깨짐 방지
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1), prop=fp)
        else:
            # 폰트 로드 실패 시 기본 설정
            plt.title(f'Lost Ark Market {title_suffix}')
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))

        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        buf = io.BytesIO()
        # savefig 시에도 다시 한 번 폰트 체크
        plt.savefig(buf, format='png', bbox_inches='tight') 
        buf.seek(0)
        plt.close()
        return buf

    @commands.command(name="악세") #임베드 이용
    async def send_price_chart(self, ctx, *, option: str = None):
        async with ctx.typing():
            try:
                # 1. 데이터 가져오기
                df = self.get_df_from_db(option)

                if df.empty:
                    return await ctx.send(f"❌ `{option if option else '데이터'}`를 찾을 수 없습니다.")

                # 2. 그래프 생성
                title_label = f"({option})" if option else "(전체)"
                image_buf = self.generate_graph(df, title_label)
                
                # 3. 디스코드 전송
                file = discord.File(fp=image_buf, filename="price_chart.png")
                embed = discord.Embed( #임베드 설정
                    title="⚖️ 경매장 시세 변동 리포트",
                    description=f"대상: **{option if option else '전체 수집 아이템'}**",
                    color=0xFFBB00
                )
                embed.set_image(url="attachment://price_chart.png")
                embed.set_footer(text="Lost Ark Market Tracker")

                await ctx.send(embed=embed, file=file)

            except Exception as e:
                await ctx.send(f"⚠️ 그래프 생성 중 오류가 발생했습니다: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.auction_acc.is_running():
            self.auction_acc.start()

async def setup(bot):
    await bot.add_cog(AuctionCog(bot))