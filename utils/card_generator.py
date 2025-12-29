from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
from .mrz_utils import MRZGenerator

class CardGenerator:
    def __init__(self, config):
        self.config = config
        self.width = config.get('width', 1000)
        self.height = config.get('height', 650)
        self.background_color = config.get('background_color', '#ffffff')
        self.header_height = config.get('header_height', 80)
        self.header_color = config.get('header_color', '#1a3a52')
        self.photo_bg_color = config.get('photo_bg_color', '#003d7a')
        
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    
    def create_blank_card(self):
        bg_rgb = self.hex_to_rgb(self.background_color)
        return Image.new('RGB', (self.width, self.height), bg_rgb)
    
    def add_header(self, card, org_name=''):
        """Add professional passport-style header"""
        draw = ImageDraw.Draw(card)
        header_rgb = self.hex_to_rgb(self.header_color)
        
        # Draw header background
        draw.rectangle(
            [(0, 0), (self.width, self.header_height)],
            fill=header_rgb
        )  # type: ignore
        
        # Add golden accent line
        draw.rectangle(
            [(0, self.header_height - 3), (self.width, self.header_height)],
            fill=(218, 165, 32)
        )  # type: ignore
        
        # Add header text
        try:
            header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            small_header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            header_font = small_header_font = ImageFont.load_default()
        
        # Main title
        draw.text((25, 15), org_name.upper() or "ID CARD", fill=(255, 255, 255), font=header_font)
        
        # Subtitle
        draw.text((25, 50), "OFFICIAL IDENTIFICATION DOCUMENT", fill=(200, 200, 200), font=small_header_font)
        
        return card
    
    def add_photo_section(self, card, photo_path):
        """Add professional photo section with blue background (like passport)"""
        draw = ImageDraw.Draw(card)
        
        # Photo background area (left side)
        photo_bg_rgb = self.hex_to_rgb(self.photo_bg_color)
        photo_section_width = 280
        photo_section_height = self.height - self.header_height - 120
        
        draw.rectangle(
            [(0, self.header_height), (photo_section_width, self.header_height + photo_section_height)],
            fill=photo_bg_rgb
        )  # type: ignore
        
        # Add photo if available
        if photo_path and os.path.exists(photo_path):
            photo = Image.open(photo_path)
            photo_size = 200
            photo.thumbnail((photo_size, photo_size), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if photo.mode != 'RGB':
                photo = photo.convert('RGB')
            
            # Center photo in section
            photo_x = (photo_section_width - photo_size) // 2
            photo_y = self.header_height + 30
            
            # Add white border around photo
            card_copy = card.copy()
            card_copy.paste(photo, (photo_x, photo_y))
            draw.rectangle(
                [(photo_x - 3, photo_y - 3), (photo_x + photo_size + 3, photo_y + photo_size + 3)],
                outline=(255, 255, 255),
                width=3
            )  # type: ignore
            card.paste(card_copy)
        
        return card
    
    def add_info_section(self, card, data):
        """Add professional information section (right side) - properly distributed vertically"""
        draw = ImageDraw.Draw(card)
        
        try:
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
            value_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            label_small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
        except:
            label_font = value_font = label_small_font = ImageFont.load_default()
        
        # Calculate available space for info section
        info_start_y = self.header_height + 15
        info_end_y = self.height - 90  # Leave space for MRZ
        available_height = info_end_y - info_start_y
        
        info_x = 300
        info_x_right = 650
        
        # Distribute items vertically
        item_spacing = available_height / 4
        
        # Label color (dark blue)
        label_color = (26, 58, 82)
        value_color = (0, 0, 0)
        
        # Row 1: SURNAME / GIVEN NAMES
        y1 = info_start_y
        draw.text((info_x, y1), "SURNAME / NOM", fill=label_color, font=label_small_font)
        surname = data.get('full_name', '').upper().split()[0] if data.get('full_name') else ''
        draw.text((info_x, y1 + 10), surname, fill=value_color, font=value_font)
        
        draw.text((info_x_right, y1), "GIVEN NAMES / PRENOM", fill=label_color, font=label_small_font)
        given_names = ' '.join(data.get('full_name', '').upper().split()[1:]) if len(data.get('full_name', '').split()) > 1 else ''
        draw.text((info_x_right, y1 + 10), given_names, fill=value_color, font=value_font)
        
        # Row 2: NATIONALITY / DATE OF BIRTH
        y2 = y1 + item_spacing
        draw.text((info_x, y2), "NATIONALITY", fill=label_color, font=label_small_font)
        draw.text((info_x, y2 + 10), data.get('organization', '')[:3].upper() or 'USA', fill=value_color, font=value_font)
        
        draw.text((info_x_right, y2), "DATE OF BIRTH", fill=label_color, font=label_small_font)
        dob = data.get('date_of_birth', '')
        draw.text((info_x_right, y2 + 10), dob, fill=value_color, font=value_font)
        
        # Row 3: PLACE OF BIRTH / ID NUMBER
        y3 = y2 + item_spacing
        draw.text((info_x, y3), "PLACE OF BIRTH", fill=label_color, font=label_small_font)
        place = data.get('address', '')[:25]
        draw.text((info_x, y3 + 10), place, fill=value_color, font=value_font)
        
        draw.text((info_x_right, y3), "ID NUMBER", fill=label_color, font=label_small_font)
        draw.text((info_x_right, y3 + 10), data.get('id_number', ''), fill=value_color, font=value_font)
        
        # Row 4: ISSUED / EXPIRES
        y4 = y3 + item_spacing
        draw.text((info_x, y4), "ISSUED", fill=label_color, font=label_small_font)
        draw.text((info_x, y4 + 10), data.get('issue_date', ''), fill=value_color, font=value_font)
        
        draw.text((info_x_right, y4), "EXPIRES", fill=label_color, font=label_small_font)
        draw.text((info_x_right, y4 + 10), data.get('expiry_date', ''), fill=value_color, font=value_font)
        
        return card
    
    def add_mrz(self, card, data):
        """Add Machine-Readable Zone (MRZ) at the bottom"""
        draw = ImageDraw.Draw(card)
        
        try:
            mrz_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        except:
            mrz_font = ImageFont.load_default()
        
        # Generate MRZ lines
        mrz_lines = MRZGenerator.format_mrz(
            data.get('full_name', 'UNKNOWN'),
            data.get('id_number', ''),
            data.get('date_of_birth', ''),
            data.get('expiry_date', '')
        )
        
        # Draw MRZ box background (dark blue)
        mrz_y_start = self.height - 80
        draw.rectangle(
            [(0, mrz_y_start - 5), (self.width, self.height)],
            fill=(26, 58, 82)
        )  # type: ignore
        
        # Draw MRZ lines in white
        mrz_x = 20
        for i, line in enumerate(mrz_lines):
            y = mrz_y_start + 15 + (i * 22)
            draw.text((mrz_x, y), line, fill=(255, 255, 255), font=mrz_font)
        
        return card
    
    def add_security_features(self, card):
        """Add subtle security feature indicators"""
        draw = ImageDraw.Draw(card)
        
        # Add subtle pattern at top right corner (hologram indicator)
        pattern_x = self.width - 120
        pattern_y = self.header_height + 20
        
        for i in range(0, 80, 5):
            draw.line([(pattern_x + i, pattern_y), (pattern_x + i + 3, pattern_y + 80)], fill=(200, 180, 100), width=1)
        
        return card
    
    def add_qr_code(self, card, qr_image_path):
        """Add QR code in bottom right"""
        if not qr_image_path or not os.path.exists(qr_image_path):
            return card
        
        qr = Image.open(qr_image_path)
        qr_size = self.config.get('qr_size', 100)
        qr.thumbnail((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if qr.mode != 'RGB':
            qr = qr.convert('RGB')
        
        qr_x = self.width - qr_size - 20
        qr_y = self.height - qr_size - 90
        
        card.paste(qr, (qr_x, qr_y))
        
        return card
    
    def generate(self, data, photo_path=None, qr_path=None, watermark_func=None):
        """Generate professional passport-style ID card"""
        card = self.create_blank_card()
        card = self.add_header(card, data.get('organization', ''))
        card = self.add_photo_section(card, photo_path)
        card = self.add_info_section(card, data)
        card = self.add_security_features(card)
        card = self.add_mrz(card, data)
        card = self.add_qr_code(card, qr_path)
        
        if watermark_func:
            card = watermark_func(card)
        
        return card
