from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os

class CardGenerator:
    def __init__(self, config):
        self.config = config
        self.width = config.get('width', 1000)
        self.height = config.get('height', 600)
        self.background_color = config.get('background_color', '#ffffff')
        self.header_height = config.get('header_height', 120)
        self.header_color = config.get('header_color', '#003366')
        
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    
    def create_blank_card(self):
        bg_rgb = self.hex_to_rgb(self.background_color)
        return Image.new('RGB', (self.width, self.height), bg_rgb)
    
    def add_header(self, card, org_name=''):
        draw = ImageDraw.Draw(card)
        header_rgb = self.hex_to_rgb(self.header_color)
        draw.rectangle(
            [(0, 0), (self.width, self.header_height)],
            fill=header_rgb
        )  # type: ignore
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        text_x = 30
        text_y = 40
        draw.text((text_x, text_y), org_name or "ID CARD", fill=(255, 255, 255), font=font)
        
        return card
    
    def add_photo(self, card, photo_path):
        if not photo_path or not os.path.exists(photo_path):
            return card
        
        photo = Image.open(photo_path)
        photo_size = 150
        photo.thumbnail((photo_size, photo_size), Image.Resampling.LANCZOS)
        
        photo_x = self.config.get('photo_x', 30)
        photo_y = self.config.get('photo_y', 160)
        card.paste(photo, (photo_x, photo_y))
        
        return card
    
    def add_text_fields(self, card, data, watermark_func=None):
        draw = ImageDraw.Draw(card)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        text_x = self.config.get('text_x', 230)
        text_y = self.config.get('text_y', 160)
        line_height = 40
        
        fields = [
            ("Name:", data.get('full_name', '')),
            ("DOB:", data.get('date_of_birth', '')),
            ("ID:", data.get('id_number', '')),
            ("Org:", data.get('organization', '')),
        ]
        
        for i, (label, value) in enumerate(fields):
            y = text_y + (i * line_height)
            draw.text((text_x, y), f"{label} {value}", fill=(0, 0, 0), font=small_font)
        
        # Add dates and signature area
        footer_y = self.height - 100
        draw.text((text_x, footer_y), f"Issue: {data.get('issue_date', '')}", fill=(0, 0, 0), font=small_font)
        draw.text((text_x, footer_y + 35), f"Expires: {data.get('expiry_date', '')}", fill=(0, 0, 0), font=small_font)
        
        if watermark_func:
            card = watermark_func(card)
        
        return card
    
    def add_qr_code(self, card, qr_image_path):
        if not qr_image_path or not os.path.exists(qr_image_path):
            return card
        
        qr = Image.open(qr_image_path)
        qr_size = self.config.get('qr_size', 120)
        qr.thumbnail((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        qr_x = self.config.get('qr_x', self.width - 150)
        qr_y = self.config.get('qr_y', self.height - 150)
        card.paste(qr, (qr_x, qr_y))
        
        return card
    
    def generate(self, data, photo_path=None, qr_path=None, watermark_func=None):
        card = self.create_blank_card()
        card = self.add_header(card, data.get('organization', ''))
        card = self.add_photo(card, photo_path)
        card = self.add_text_fields(card, data, watermark_func)
        card = self.add_qr_code(card, qr_path)
        return card
