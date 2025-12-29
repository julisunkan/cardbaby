import qrcode
import os

class QRCodeGenerator:
    def __init__(self, output_dir='static/qrcodes'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(self, data, filename=None):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        if filename is None:
            filename = f"qr_{data.replace('/', '_')}.png"
        
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)
        
        return filepath
