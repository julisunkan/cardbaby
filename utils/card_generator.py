from PIL import Image, ImageDraw, ImageFont
import os
import base64
from io import BytesIO
from .mrz_utils import MRZGenerator

class CardGenerator:
    def __init__(self, config):
        self.config = config
        self.width = config.get('width', 600)  # Pocket size width
        self.height = config.get('height', 380) # Pocket size height
        self.background_color = config.get('background_color', '#ffffff')
        self.header_height = config.get('header_height', 60)
        self.header_color = config.get('header_color', '#1a3a52')
        self.photo_bg_color = config.get('photo_bg_color', '#003d7a')
        
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    
    def create_blank_card(self, background_path=None):
        if background_path and os.path.exists(background_path):
            try:
                bg = Image.open(background_path)
                return bg.resize((self.width, self.height), Image.Resampling.LANCZOS).convert('RGB')
            except Exception as e:
                print(f"Error loading background image: {e}")
        
        bg_rgb = self.hex_to_rgb(self.background_color)
        return Image.new('RGB', (self.width, self.height), bg_rgb)
    
    def add_header(self, card, org_name='', logo_path=None):
        draw = ImageDraw.Draw(card)
        header_rgb = self.hex_to_rgb(self.header_color)
        
        # Override header color based on theme if set in config/data
        # This is a bit of a hack since we don't have a clean theme-to-color mapping in CardGenerator yet
        # But for MVP it works
        draw.rectangle((0, 0, self.width, self.header_height), fill=header_rgb)
        
        # Accent line color
        accent_color = (218, 165, 32) # Gold default
        draw.rectangle((0, self.header_height - 2, self.width, self.header_height), fill=accent_color)
        
        text_x_offset = 15
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path)
                logo_size = self.header_height - 15
                logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
                if logo.mode != 'RGBA': logo = logo.convert('RGBA')
                logo_bg = Image.new('RGBA', logo.size, (255, 255, 255, 255))
                logo_bg.paste(logo, (0, 0), logo)
                logo = logo_bg.convert('RGB')
                card.paste(logo, (15, 7))
                text_x_offset = 15 + logo_size + 10
            except Exception as e:
                print(f'Error adding logo: {e}')

        try:
            header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            small_header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            header_font = small_header_font = ImageFont.load_default()
        
        draw.text((text_x_offset, 10), org_name.upper() or "ID CARD", fill=(255, 255, 255), font=header_font)
        draw.text((text_x_offset, 35), "OFFICIAL IDENTIFICATION DOCUMENT", fill=(200, 200, 200), font=small_header_font)
        return card
    
    def add_photo_section(self, card, photo_path):
        photo_section_width = 160
        photo_section_height = self.height - self.header_height - 60
        
        # We don't draw a solid rectangle background anymore to allow blending with card background
        
        if photo_path and os.path.exists(photo_path):
            try:
                # Optimized background removal
                from rembg import remove, new_session
                if not hasattr(self, '_rembg_session'):
                    self._rembg_session = new_session("u2net_is") # Faster lightweight model
                
                with open(photo_path, 'rb') as i:
                    photo = remove(i.read(), session=self._rembg_session)
                    photo = Image.open(BytesIO(photo))
                
                photo_size = 120
                photo.thumbnail((photo_size, photo_size), Image.Resampling.LANCZOS)
                
                # Convert to RGBA to ensure transparency is preserved
                if photo.mode != 'RGBA':
                    photo = photo.convert('RGBA')
                
                photo_x = (photo_section_width - photo_size) // 2
                photo_y = self.header_height + 20
                
                # Draw a subtle border instead of a background rectangle
                draw = ImageDraw.Draw(card)
                draw.rectangle((photo_x - 2, photo_y - 2, photo_x + photo_size + 2, photo_y + photo_size + 2), outline=(255, 255, 255), width=2)
                
                # Paste with alpha mask to preserve transparency
                card.paste(photo, (photo_x, photo_y), photo)
            except Exception as e:
                print(f'Error adding photo: {e}')
                # Fallback to simple chroma keying if rembg fails
                try:
                    photo = Image.open(photo_path)
                    photo.thumbnail((120, 120), Image.Resampling.LANCZOS)
                    if photo.mode != 'RGBA': photo = photo.convert('RGBA')
                    data = photo.getdata()
                    new_data = []
                    for item in data:
                        if item[0] > 240 and item[1] > 240 and item[2] > 240:
                            new_data.append((255, 255, 255, 0))
                        else:
                            new_data.append(item)
                    photo.putdata(new_data)
                    photo_x = (photo_section_width - 120) // 2
                    photo_y = self.header_height + 20
                    card.paste(photo, (photo_x, photo_y), photo)
                except:
                    pass
        return card
    
    def add_info_section(self, card, data):
        draw = ImageDraw.Draw(card)
        font_family = data.get('font_family', 'DejaVuSans')
        font_size = int(data.get('font_size', 10))
        font_color_hex = data.get('font_color', '#000000')
        font_bold = data.get('font_bold') in ['on', True, 'true']
        font_italic = data.get('font_italic') in ['on', True, 'true']
        
        value_color = self.hex_to_rgb(font_color_hex)
        label_color = (26, 58, 82) # Keeping labels professional but could be customized too
        
        font_dir = "/usr/share/fonts/truetype/liberation/" if "Liberation" in font_family else "/usr/share/fonts/truetype/dejavu/"
        
        # Determine font path based on bold/italic
        suffix = ""
        if font_bold and font_italic: suffix = "BoldItalic"
        elif font_bold: suffix = "Bold"
        elif font_italic: suffix = "Italic"
        
        # Try to find the specific font variant, fallback to base font
        if suffix:
            font_filename = f"{font_family}-{suffix}.ttf"
        else:
            font_filename = f"{font_family}.ttf"
        font_path = os.path.join(font_dir, font_filename)
        
        if not os.path.exists(font_path):
            font_path = os.path.join(font_dir, f"{font_family}.ttf")

        try:
            # For labels, we prefer Bold if available, otherwise fallback to our main font_path
            label_bold_path = os.path.join(font_dir, f"{font_family}-Bold.ttf")
            label_font_path = label_bold_path if os.path.exists(label_bold_path) else font_path
            
            label_font = ImageFont.truetype(label_font_path, max(7, font_size - 2))
            value_font = ImageFont.truetype(font_path, font_size)
            label_small_font = ImageFont.truetype(font_path, max(6, font_size - 4))
        except:
            label_font = value_font = label_small_font = ImageFont.load_default()
        
        info_start_y = self.header_height + 10
        info_end_y = self.height - 80 
        available_height = info_end_y - info_start_y
        info_x, info_x_right = 180, 400
        item_spacing = available_height / 4
        
        y1 = info_start_y
        draw.text((info_x, y1), "SURNAME / NOM", fill=label_color, font=label_small_font)
        draw.text((info_x, y1 + 10), data.get('full_name', '').upper().split()[0] if data.get('full_name') else '', fill=value_color, font=value_font)
        draw.text((info_x_right, y1), "GIVEN NAMES / PRENOM", fill=label_color, font=label_small_font)
        draw.text((info_x_right, y1 + 10), ' '.join(data.get('full_name', '').upper().split()[1:]) if len(data.get('full_name', '').split()) > 1 else '', fill=value_color, font=value_font)
        
        y2 = y1 + item_spacing
        draw.text((info_x, y2), "NATIONALITY", fill=label_color, font=label_small_font)
        draw.text((info_x, y2 + 10), data.get('organization', '')[:3].upper() or 'USA', fill=value_color, font=value_font)
        draw.text((info_x_right, y2), "DATE OF BIRTH", fill=label_color, font=label_small_font)
        draw.text((info_x_right, y2 + 10), data.get('date_of_birth', ''), fill=value_color, font=value_font)
        
        y3 = y2 + item_spacing
        draw.text((info_x, y3), "PLACE OF BIRTH", fill=label_color, font=label_small_font)
        draw.text((info_x, y3 + 10), data.get('address', '')[:20], fill=value_color, font=value_font)
        draw.text((info_x_right, y3), "ID NUMBER", fill=label_color, font=label_small_font)
        draw.text((info_x_right, y3 + 10), data.get('id_number', ''), fill=value_color, font=value_font)
        
        y4 = y3 + item_spacing
        draw.text((info_x, y4), "ISSUED", fill=label_color, font=label_small_font)
        draw.text((info_x, y4 + 10), data.get('issue_date', ''), fill=value_color, font=value_font)
        draw.text((info_x_right, y4), "EXPIRES", fill=label_color, font=label_small_font)
        draw.text((info_x_right, y4 + 10), data.get('expiry_date', ''), fill=value_color, font=value_font)

        sig_data = data.get('signature')
        if sig_data and sig_data.startswith('data:image/png;base64,'):
            try:
                sig_content = base64.b64decode(sig_data.split(',')[1])
                sig_img = Image.open(BytesIO(sig_content))
                sig_img.thumbnail((120, 40), Image.Resampling.LANCZOS)
                sig_x, sig_y = info_x, self.height - 110
                if sig_img.mode == 'RGBA': card.paste(sig_img, (sig_x, sig_y), sig_img)
                else: card.paste(sig_img, (sig_x, sig_y))
                draw.text((sig_x, sig_y + 45), "HOLDER SIGNATURE", fill=label_color, font=label_small_font)
            except Exception as e:
                print(f'Error adding signature: {e}')
        return card

    def add_mrz(self, card, data):
        draw = ImageDraw.Draw(card)
        try: mrz_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
        except: mrz_font = ImageFont.load_default()
        mrz_text = MRZGenerator.format_mrz(data.get('full_name', 'UNKNOWN'), data.get('id_number', ''), data.get('date_of_birth', ''), data.get('expiry_date', ''))
        
        mrz_y_start = self.height - 35 # Adjusted for single line
        draw.rectangle((0, mrz_y_start - 3, self.width, self.height), fill=(26, 58, 82))
        mrz_x = 10
        draw.text((mrz_x, mrz_y_start + 5), mrz_text, fill=(255, 255, 255), font=mrz_font)
        return card

    def add_security_features(self, card):
        draw = ImageDraw.Draw(card)
        pattern_x, pattern_y = self.width - 120, self.header_height + 20
        for i in range(0, 80, 5):
            draw.line((pattern_x + i, pattern_y, pattern_x + i + 3, pattern_y + 80), fill=(200, 180, 100), width=1)
        return card

    def add_qr_code(self, card, qr_image_path):
        if not qr_image_path or not os.path.exists(qr_image_path): return card
        try:
            qr = Image.open(qr_image_path)
            qr_size = 60
            qr.thumbnail((qr_size, qr_size), Image.Resampling.LANCZOS)
            if qr.mode != 'RGB': qr = qr.convert('RGB')
            qr_x, qr_y = self.width - qr_size - 15, self.height - qr_size - 60
            card.paste(qr, (qr_x, qr_y))
        except Exception as e:
            print(f'Error adding QR: {e}')
        return card

    def generate(self, data, photo_path=None, qr_path=None, watermark_func=None, logo_path=None, background_path=None):
        card = self.create_blank_card(background_path)
        card = self.add_header(card, data.get('organization', ''), logo_path)
        card = self.add_photo_section(card, photo_path)
        card = self.add_info_section(card, data)
        card = self.add_security_features(card)
        card = self.add_mrz(card, data)
        card = self.add_qr_code(card, qr_path)
        if watermark_func: card = watermark_func(card)
        return card
