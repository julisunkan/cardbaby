#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('static/icons', exist_ok=True)

def create_icon(size, maskable=False):
    """Generate PWA icon"""
    bg_color = (255, 255, 255) if not maskable else (220, 53, 69)
    img = Image.new('RGBA', (size, size), bg_color if maskable else (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    if maskable:
        # Solid color background for maskable icons
        draw.rectangle([(0, 0), (size, size)], fill=(220, 53, 69))
    else:
        # Gradient background
        for i in range(size):
            r = int(220 - (i / size) * 50)
            g = int(53 + (i / size) * 100)
            b = int(69 + (i / size) * 100)
            draw.line([(0, i), (size, i)], fill=(r, g, b))
    
    # Draw card icon
    card_margin = size // 8
    card_color = (255, 255, 255) if not maskable else (255, 255, 255)
    
    # Card background
    draw.rectangle(
        [(card_margin, card_margin), (size - card_margin, size - card_margin)],
        fill=card_color,
        outline=(40, 167, 69) if not maskable else (255, 255, 255),
        width=3
    )
    
    # Top bar (like card header)
    bar_height = size // 6
    bar_color = (40, 167, 69) if not maskable else (40, 167, 69)
    draw.rectangle(
        [(card_margin, card_margin), (size - card_margin, card_margin + bar_height)],
        fill=bar_color
    )
    
    # Add text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(12, size // 20))
    except:
        font = ImageFont.load_default()
    
    text = "ID"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = (bar_height - text_height) // 2 + card_margin
    
    draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
    
    return img

# Generate 192x192
print("Generating 192x192 icon...")
icon_192 = create_icon(192)
icon_192.save('static/icons/icon-192.png')

# Generate 512x512
print("Generating 512x512 icon...")
icon_512 = create_icon(512)
icon_512.save('static/icons/icon-512.png')

# Generate maskable icons
print("Generating maskable icons...")
maskable_192 = create_icon(192, maskable=True)
maskable_192.save('static/icons/icon-maskable-192.png')

maskable_512 = create_icon(512, maskable=True)
maskable_512.save('static/icons/icon-maskable-512.png')

# Generate screenshot
print("Generating screenshot...")
screenshot = Image.new('RGB', (540, 720), (255, 255, 255))
draw = ImageDraw.Draw(screenshot)

# Header
draw.rectangle([(0, 0), (540, 80)], fill=(220, 53, 69))
try:
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
except:
    font_large = ImageFont.load_default()

draw.text((20, 20), "ID Card Generator", fill=(255, 255, 255), font=font_large)

# Content area
draw.rectangle([(20, 100), (520, 360)], outline=(220, 53, 69), width=2, fill=(245, 245, 245))
try:
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except:
    font_small = ImageFont.load_default()

draw.text((40, 120), "Generate Professional ID Cards", fill=(220, 53, 69), font=font_small)
draw.text((40, 160), "✓ Passport-style design", fill=(40, 167, 69), font=font_small)
draw.text((40, 200), "✓ Auto-generated ID numbers", fill=(40, 167, 69), font=font_small)
draw.text((40, 240), "✓ QR code verification", fill=(40, 167, 69), font=font_small)
draw.text((40, 280), "✓ PNG & PDF export", fill=(40, 167, 69), font=font_small)

# Button area
draw.rectangle([(50, 400), (490, 470)], fill=(255, 193, 7))
draw.text((180, 420), "Generate Card", fill=(0, 0, 0), font=font_small)

screenshot.save('static/icons/screenshot-540x720.png')

print("✓ All icons generated successfully!")
print("  - icon-192.png")
print("  - icon-512.png")
print("  - icon-maskable-192.png")
print("  - icon-maskable-512.png")
print("  - screenshot-540x720.png")
