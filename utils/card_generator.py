from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
from .mrz_utils import MRZGenerator

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
        
        # Draw main header with gradient effect using lines
        for i in range(self.header_height):
            # Subtle gradient
            intensity = int(header_rgb[0] - (i * 0.1))
            intensity = max(0, min(255, intensity))
            color = (intensity, int(header_rgb[1] - (i * 0.05)), int(header_rgb[2] - (i * 0.05)))
            draw.line([(0, i), (self.width, i)], fill=color)
        
        # Add decorative bottom border
        draw.rectangle(
            [(0, self.header_height - 4), (self.width, self.header_height)],
            fill=(255, 215, 0)
        )  # type: ignore
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        except:
            font = ImageFont.load_default()
        
        text_x = 30
        text_y = 35
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
            bold_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            tiny_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
        except:
            bold_font = font = small_font = tiny_font = ImageFont.load_default()
        
        text_x = self.config.get('text_x', 230)
        text_y = self.config.get('text_y', 160)
        line_height = 40
        
        # Primary text fields with colors
        fields = [
            ("NAME:", data.get('full_name', ''), bold_font, (0, 0, 0)),
            ("DOB:", data.get('date_of_birth', ''), font, (20, 20, 60)),
            ("ID NO:", data.get('id_number', ''), bold_font, (0, 0, 0)),
            ("ORG:", data.get('organization', ''), font, (20, 20, 60)),
        ]
        
        for i, (label, value, fnt, color) in enumerate(fields):
            y = text_y + (i * line_height)
            draw.text((text_x, y), label, fill=color, font=fnt)
            draw.text((text_x + 140, y), value, fill=(0, 0, 0), font=font)
        
        # Add dates section with accent color
        footer_y = self.height - 140
        issue_y = footer_y
        expire_y = footer_y + 35
        
        accent_color = self.hex_to_rgb(self.header_color)
        draw.text((text_x, issue_y), "ISSUED:", fill=accent_color, font=small_font)
        draw.text((text_x + 120, issue_y), data.get('issue_date', ''), fill=(0, 0, 0), font=small_font)
        
        draw.text((text_x, expire_y), "EXPIRES:", fill=accent_color, font=small_font)
        draw.text((text_x + 130, expire_y), data.get('expiry_date', ''), fill=(0, 0, 0), font=small_font)
        
        if watermark_func:
            card = watermark_func(card)
        
        return card
    
    def add_mrz(self, card, data):
        """Add Machine-Readable Zone (MRZ) to the bottom of the card"""
        draw = ImageDraw.Draw(card)
        
        try:
            mrz_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
        except:
            mrz_font = ImageFont.load_default()
        
        # Generate MRZ lines
        mrz_lines = MRZGenerator.format_mrz(
            data.get('full_name', 'UNKNOWN'),
            data.get('id_number', ''),
            data.get('date_of_birth', ''),
            data.get('expiry_date', '')
        )
        
        # Draw MRZ box background
        mrz_y_start = self.height - 65
        mrz_bg_color = (240, 240, 240)
        draw.rectangle(
            [(10, mrz_y_start - 5), (self.width - 10, self.height - 5)],
            fill=mrz_bg_color,
            outline=(100, 100, 100)
        )  # type: ignore
        
        # Draw MRZ lines
        mrz_x = 20
        for i, line in enumerate(mrz_lines):
            y = mrz_y_start + (i * 20)
            draw.text((mrz_x, y), line, fill=(0, 0, 0), font=mrz_font)
        
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
        card = self.add_mrz(card, data)
        card = self.add_qr_code(card, qr_path)
        return card
