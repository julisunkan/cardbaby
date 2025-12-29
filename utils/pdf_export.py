from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
import os

class PDFExporter:
    def __init__(self, output_dir='static/pdfs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export(self, card_image_path, data, filename=None):
        if filename is None:
            filename = f"card_{data.get('id_number', 'unknown')}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"ID Card: {data.get('full_name', '')}")
        
        # Add image
        if os.path.exists(card_image_path):
            img = ImageReader(card_image_path)
            c.drawImage(img, 50, height - 400, width=500, height=300, preserveAspectRatio=True)
        
        # Add info
        c.setFont("Helvetica", 10)
        y = height - 450
        info_lines = [
            f"ID Number: {data.get('id_number', '')}",
            f"Name: {data.get('full_name', '')}",
            f"Organization: {data.get('organization', '')}",
            f"Date of Birth: {data.get('date_of_birth', '')}",
            f"Issue Date: {data.get('issue_date', '')}",
            f"Expiry Date: {data.get('expiry_date', '')}",
            f"Address: {data.get('address', '')}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        for line in info_lines:
            c.drawString(50, y, line)
            y -= 15
        
        c.save()
        return filepath
