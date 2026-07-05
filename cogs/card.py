import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

import discord
from discord.ext import commands
from discord import app_commands

# 만약 config.py가 cogs 폴더가 아닌 상위 폴더(루트)에 있다면 경로를 맞춰야 합니다.
# 아래 구조는 config.py가 루트 폴더에 있고, cogs/ 폴더에서 불러오는 상황을 가정한 예시입니다.
from config import API_KEY


class CharacterCard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_character_data(self, username):
        url = f'https://developer-lostark.game.onstove.com/armories/characters/{username}'
        headers = {'accept': 'application/json', 'authorization': API_KEY}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return None
            character_data = response.json()
            return character_data
        except Exception as e:
            print(f"오류 발생: {e}")
            return None

    def create_profile_card(self, character_data):
        # 입력 데이터 구조 변경 및 아크 패시브 데이터 추출
        profile_data = character_data.get('ArmoryProfile', {})
        ark_passive_dict = character_data.get('ArkPassive')
        arkPassive = ark_passive_dict.get(
            'Title') if ark_passive_dict else None

        # 1. 기본 캔버스 및 이중 레이어 카드 배경 설정
        width, height = 450, 720
        outer_bg = (11, 12, 15, 255)
        card = Image.new('RGBA', (width, height), color=outer_bg)
        draw = ImageDraw.Draw(card)

        card_body_color = (19, 21, 26, 255)
        draw.rounded_rectangle(
            [12, 12, width-12, height-12], radius=16, fill=card_body_color)

        # 2. 경로 설정: 봇 메인 실행 파일 위치 기준으로 고정하거나, 현재 파일 기준으로 설정
        # 팁: 이미지/폰트 폴더가 루트 폴더에 있다면 아래 base_dir를 수정해야 할 수 있습니다.
        base_dir = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))  # cogs 상위 폴더(루트) 기준
        font_dir = os.path.join(base_dir, "font")
        img_dir = os.path.join(base_dir, "img")

        try:
            font_title = ImageFont.truetype(os.path.join(
                font_dir, "Pretendard-Regular.otf"), 15)
            font_name = ImageFont.truetype(
                os.path.join(font_dir, "Pretendard-Bold.otf"), 32)
            font_class = ImageFont.truetype(os.path.join(
                font_dir, "Pretendard-Medium.otf"), 17)
            font_badge = ImageFont.truetype(os.path.join(
                font_dir, "Pretendard-Medium.otf"), 13)
            font_value = ImageFont.truetype(
                os.path.join(font_dir, "Pretendard-Bold.otf"), 17)
        except IOError:
            print(f"⚠️ {font_dir} 내 폰트 로드 실패로 시스템 기본 서체로 대체합니다.")
            try:
                font_title = font_class = font_badge = ImageFont.truetype(
                    "malgun.ttf", 15)
                font_name = ImageFont.truetype("malgunbd.ttf", 32)
                font_value = ImageFont.truetype("malgunbd.ttf", 17)
            except IOError:
                font_title = font_name = font_class = font_badge = font_value = ImageFont.load_default()

        # 3. 캐릭터 이미지 로드 및 마스킹 연산
        try:
            image_url = profile_data.get('CharacterImage')
            if not image_url:
                raise ValueError("CharacterImage URL이 없습니다.")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()

            char_img = Image.open(BytesIO(response.content)).convert('RGBA')
            orig_w, orig_h = char_img.size

            zoom_factor = 0.58
            crop_w = int(orig_w * zoom_factor)
            crop_left = (orig_w - crop_w) // 2
            crop_right = crop_left + crop_w
            crop_h = int(orig_h * 0.75)
            char_img = char_img.crop((crop_left, 0, crop_right, crop_h))

            target_w = 450
            target_h = int(crop_h * (target_w / crop_w))
            char_img = char_img.resize(
                (target_w, target_h), Image.Resampling.LANCZOS)

            blurred_char = char_img.filter(ImageFilter.GaussianBlur(radius=10))
            blur_mask = Image.new('L', char_img.size, 0)
            blur_mask_draw = ImageDraw.Draw(blur_mask)

            blur_start_y = 390
            blur_end_y = min(550, target_h)

            if blur_start_y < target_h:
                for y in range(blur_start_y, blur_end_y):
                    alpha = int(255 * (y - blur_start_y) /
                                (blur_end_y - blur_start_y))
                    blur_mask_draw.line([(0, y), (target_w, y)], fill=alpha)
                if blur_end_y < target_h:
                    blur_mask_draw.rectangle(
                        [0, blur_end_y, target_w, target_h], fill=255)

            final_char = Image.composite(blurred_char, char_img, blur_mask)

            char_canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            char_canvas.paste(final_char, (0, 0))

            canvas_mask = Image.new('L', (width, height), 0)
            canvas_mask_draw = ImageDraw.Draw(canvas_mask)
            canvas_mask_draw.rounded_rectangle(
                [23, 23, width-23, height-23], radius=14, fill=255)

            char_alpha = char_canvas.split()[3]
            combined_mask = ImageChops.multiply(char_alpha, canvas_mask)

            card.paste(char_canvas, (0, 0), combined_mask)

        except Exception as e:
            print(f"⚠️ 캐릭터 이미지 처리 스킵 (사유: {e})")

        # 4. 하단 배경 오버레이 그라데이션
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        grad_draw = ImageDraw.Draw(gradient)
        grad_start_y = 320
        grad_end_y = 530
        for y in range(grad_start_y, grad_end_y):
            alpha = int(255 * (y - grad_start_y) / (grad_end_y - grad_start_y))
            grad_draw.line([(0, y), (width, y)], fill=(
                card_body_color[0], card_body_color[1], card_body_color[2], alpha))
        grad_draw.rectangle([0, grad_end_y, width, height],
                            fill=card_body_color)
        card = Image.alpha_composite(card, gradient)
        draw = ImageDraw.Draw(card)

        # 5. 프리미엄 UI 요소 드로잉
        grey_border_color = (45, 48, 58, 255)
        draw.rounded_rectangle(
            [12, 12, width-12, height-12], radius=16, outline=grey_border_color, width=1)

        gold_grad = Image.new('RGBA', (width, height))
        g_draw = ImageDraw.Draw(gold_grad)
        max_diagonal = width + height

        for i in range(max_diagonal):
            mix = i / max_diagonal
            if mix < 0.08:
                sub = mix / 0.08
                r = int(255 - (255 - 250) * sub)
                g = int(255 - (255 - 222) * sub)
                b = int(245 - (245 - 148) * sub)
            elif mix < 0.40:
                sub = (mix - 0.08) / (0.40 - 0.08)
                r = int(250 - (250 - 200) * sub)
                g = int(222 - (222 - 162) * sub)
                b = int(148 - (148 - 72) * sub)
            elif mix < 0.82:
                sub = (mix - 0.40) / (0.82 - 0.40)
                r = int(200 - (200 - 105) * sub)
                g = int(162 - (162 - 78) * sub)
                b = int(72 - (72 - 38) * sub)
            else:
                sub = (mix - 0.82) / (1.0 - 0.82)
                r = int(105 + (170 - 105) * sub)
                g = int(78 + (135 - 78) * sub)
                b = int(38 + (65 - 38) * sub)
            g_draw.line([(i, 0), (0, i)], fill=(r, g, b, 255))

        gold_mask = Image.new('L', (width, height), 0)
        gold_mask_draw = ImageDraw.Draw(gold_mask)
        gold_mask_draw.rounded_rectangle(
            [22, 22, width-22, height-22], radius=14, fill=255)
        gold_mask_draw.rounded_rectangle(
            [24, 24, width-24, height-24], radius=12, fill=0)
        card.paste(gold_grad, (0, 0), gold_mask)

        # 5-3. 클래스 엠블럼
        emb_cx, emb_cy = 375, 65
        class_name = profile_data.get('CharacterClassName', '클래스명')
        emblem_path = os.path.join(img_dir, "class", f"{class_name}.png")
        target_emblem_size = (50, 50)

        if os.path.exists(emblem_path):
            try:
                emblem_img = Image.open(emblem_path).convert('RGBA')
                emblem_img = emblem_img.resize(
                    target_emblem_size, Image.Resampling.LANCZOS)
                paste_x = emb_cx - (target_emblem_size[0] // 2)
                paste_y = emb_cy - (target_emblem_size[1] // 2) - 2
                card.paste(emblem_img, (paste_x, paste_y), emblem_img)
            except Exception as e:
                print(f"⚠️ 클래스 엠블럼 이미지 로드 후 처리 도중 오류 발생: {e}")
        else:
            draw.arc([emb_cx-12, emb_cy-12, emb_cx+12, emb_cy+12],
                     start=0, end=360, fill=(210, 215, 225, 180), width=1)

        # 6. 상단 서버 이름 뱃지
        bx1, by1, bx2, by2 = 36, 36, 115, 62
        draw.rounded_rectangle([bx1, by1, bx2, by2],
                               radius=4, fill=(32, 35, 43, 255))
        server_cx = (bx1 + bx2) / 2
        server_cy = (by1 + by2) / 2
        draw.text((server_cx, server_cy), profile_data.get(
            'ServerName', '서버명'), font=font_badge, fill=(160, 165, 175, 255), anchor="mm")

        # 7. 중앙 캐릭터 텍스트 정보
        text_start_y = 445
        draw.text((48, text_start_y), profile_data.get(
            'Title', '칭호 없음'), font=font_title, fill=(160, 165, 175, 255))
        draw.text((46, text_start_y + 24), profile_data.get('CharacterName',
                  '캐릭터명'), font=font_name, fill=(255, 255, 255, 255))

        class_y = text_start_y + 69
        class_text = f"{class_name} | {arkPassive}" if arkPassive else class_name
        draw.text((48, class_y), class_text,
                  font=font_class, fill=(200, 205, 215, 255))

        honor_val = profile_data.get('HonorPoint', 0)
        try:
            honor_score = int(float(str(honor_val).replace(',', '')))
        except ValueError:
            honor_score = 0

        level_str = str(honor_val)
        text_w = font_class.getbbox(
            level_str)[2] - font_class.getbbox(level_str)[0]
        text_base_x = 364
        draw.text((text_base_x - text_w, class_y - 1), level_str,
                  font=font_class, fill=(210, 215, 225, 255))

        badge_filename = "honor1.png"
        if honor_score >= 1000:
            badge_filename = "honor5.png"
        elif honor_score >= 500:
            badge_filename = "honor4.png"
        elif honor_score >= 300:
            badge_filename = "honor3.png"
        elif honor_score >= 100:
            badge_filename = "honor2.png"

        badge_path = os.path.join(img_dir, "honor", badge_filename)

        if os.path.exists(badge_path):
            try:
                badge_img = Image.open(badge_path).convert('RGBA')
                badge_img = badge_img.resize(
                    (30, 26), Image.Resampling.LANCZOS)
                card.paste(badge_img, (text_base_x +
                           6, class_y - 3), badge_img)
            except Exception as e:
                print(f"⚠️ 뱃지 이미지 처리 도중 오류 발생: {e}")
        else:
            bx, by = 378, class_y + 2
            draw.polygon([(bx+8, by), (bx+15, by+5), (bx+15, by+13), (bx+8, by+18), (bx,
                         by+13), (bx, by+5)], fill=(65, 80, 105, 255), outline=(140, 160, 195, 255))

        # 8. 하단 프리미엄 대시보드 스펙 정보창
        info_box_y = 555
        draw.rounded_rectangle([32, info_box_y, width-32, height-32], radius=8,
                               fill=(20, 22, 27, 255), outline=(38, 41, 51, 255), width=1)

        def draw_badge_item(x, y, label, value, label_width=80):
            badge_height = 26
            draw.rounded_rectangle(
                [x, y, x + label_width, y + badge_height], radius=4, fill=(34, 36, 44, 255))
            box_cx = x + (label_width / 2)
            box_cy = y + (badge_height / 2)
            draw.text((box_cx, box_cy), label, font=font_badge,
                      fill=(150, 155, 165, 255), anchor="mm")
            draw.text((x + label_width + 12, box_cy), str(value),
                      font=font_value, fill=(240, 242, 245, 255), anchor="lm")

        draw_badge_item(48, info_box_y + 16, "길드",
                        profile_data.get('GuildName', '-'), label_width=60)
        draw_badge_item(48, info_box_y + 54, "아이템 Lv",
                        profile_data.get('ItemAvgLevel', '0'), label_width=75)
        draw_badge_item(240, info_box_y + 54, "전투력",
                        profile_data.get('CombatPower', '-'), label_width=65)
        draw_badge_item(48, info_box_y + 92, "원정대 Lv",
                        profile_data.get('ExpeditionLevel', '0'), label_width=75)
        draw_badge_item(240, info_box_y + 92, "PVP",
                        profile_data.get('PvpRank', '-'), label_width=65)

        # 10. 이미지 버퍼 출력 반환
        image_buffer = BytesIO()
        card.save(image_buffer, format='PNG')
        image_buffer.seek(0)

        return image_buffer

    # --- 디스코드 슬래시 명령어 부분 ---
    @app_commands.command(name="캐릭터카드", description="로스트아크 캐릭터 프로필 카드를 생성합니다.")
    @app_commands.describe(nickname="조회할 캐릭터의 닉네임")
    async def character_card(self, interaction: discord.Interaction, nickname: str):
        # API 조회 및 이미지 생성이 오래 걸릴 수 있으므로 봇이 생각 중인 상태로 만듦
        await interaction.response.defer()

        # 데이터 가져오기 (동기 함수이므로 스레드 분리를 고려할 수 있으나 기본 구현 유지)
        api_data = self.get_character_data(nickname)

        if not api_data:
            await interaction.followup.send(f"❌ `{nickname}` 캐릭터 정보를 찾을 수 없거나 API 오류가 발생했습니다.", ephemeral=True)
            return

        # 이미지 생성
        try:
            final_image_io = self.create_profile_card(api_data)

            # 디스코드 파일 객체 생성
            discord_file = discord.File(
                fp=final_image_io, filename=f"{nickname}_card.png")

            # 결과 전송
            await interaction.followup.send(file=discord_file)

        except Exception as e:
            await interaction.followup.send(f"❌ 카드 생성 중 오류가 발생했습니다.", ephemeral=True)
            print(f"디스코드 연동 중 에러 발생: {e}")


# Cog 등록 함수
async def setup(bot: commands.Bot):
    await bot.add_cog(CharacterCard(bot))
