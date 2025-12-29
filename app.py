from flask import Flask, render_template, request, jsonify, session, redirect, send_file, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import time
from apscheduler.schedulers.background import BackgroundScheduler

from models import db, IDCard, CardTemplate, Watermark, AuditLog, AdminUser
from utils.card_generator import CardGenerator
from utils.qr_utils import QRCodeGenerator
from utils.pdf_export import PDFExporter
from utils.mrz_utils import MRZGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///idcards.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db.init_app(app)

# Initialize QR and PDF utilities
qr_gen = QRCodeGenerator('static/qrcodes')
pdf_exporter = PDFExporter('static/pdfs')

# Create necessary directories
for folder in ['static/uploads', 'static/qrcodes', 'static/cards', 'static/pdfs', 'static/flags']:
    os.makedirs(folder, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_audit_log(action, card_id=None, details=''):
    user = 'anonymous'
    log = AuditLog(admin_user=user, action=action, card_id=card_id, details=details)
    db.session.add(log)
    db.session.commit()

def apply_watermark(card_image, watermark_text, color, opacity, position):
    """Apply watermark to card image"""
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(card_image)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    color_str = color.lstrip('#')
    color_rgb = (int(color_str[0:2], 16), int(color_str[2:4], 16), int(color_str[4:6], 16))
    
    width, height = card_image.size
    
    if position == 'top':
        y = 50
    elif position == 'bottom':
        y = height - 120
    else:  # center
        y = height // 2 - 40
    
    # Draw with transparency effect
    x = width // 2 - len(watermark_text) * 20
    draw.text((x, y), watermark_text, fill=color_rgb, font=font)
    
    return card_image


@app.route('/')
def index():
    templates = CardTemplate.query.filter_by(is_active=True).all()
    return render_template('index.html', templates=templates)

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js')

@app.route('/api/generate-id')
def generate_id():
    id_number = MRZGenerator.generate_id_number()
    return jsonify({'id_number': id_number})

@app.route('/generate', methods=['POST'])
def generate_card():
    try:
        data = request.form.to_dict()
        template_id = request.form.get('template_id', 1)
        
        # Get template
        template = CardTemplate.query.filter_by(id=template_id).first()
        if not template:
            return jsonify({'error': 'Template not found'}), 400
        
        config = template.get_config()
        
        # Handle photo and logo uploads
        photo_filename = None
        logo_filename = None
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().timestamp()}_photo_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_filename = filename

        if 'logo' in request.files:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().timestamp()}_logo_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logo_filename = filename
        
        # Check if card already exists
        existing = IDCard.query.filter_by(id_number=data.get('id_number')).first()
        if existing:
            return jsonify({'error': 'ID number already exists'}), 400
        
        # Generate QR code
        qr_path = qr_gen.generate(f"/verify/{data.get('id_number')}", 
                                   f"qr_{data.get('id_number')}.png")
        
        # Generate card image
        card_gen = CardGenerator(config)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename) if photo_filename else None
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename) if logo_filename else None
        
        background_filename = data.get('background_image')
        background_path = os.path.join('static/backgrounds', background_filename) if background_filename else None
        
        # Prepare watermark function
        watermark_obj = Watermark.query.first()
        if watermark_obj and watermark_obj.enabled:
            def watermark_func(card):  # type: ignore
                return apply_watermark(card, watermark_obj.text, watermark_obj.color, 
                                     watermark_obj.opacity, watermark_obj.position)
        else:
            watermark_func = None  # type: ignore
        
        card_image = card_gen.generate(data, photo_path, qr_path, watermark_func, logo_path, background_path)
        
        # Save card image
        card_filename = f"card_{data.get('id_number')}.png"
        card_path = os.path.join('static/cards', card_filename)
        card_image.save(card_path)
        
        # Export to PDF
        pdf_filename = f"card_{data.get('id_number')}.pdf"
        pdf_path = pdf_exporter.export(card_path, data, pdf_filename)
        
        # Save to database
        id_card = IDCard(
            id_number=data.get('id_number'),
            full_name=data.get('full_name'),
            date_of_birth=datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date(),
            organization=data.get('organization'),
            address=data.get('address'),
            issue_date=datetime.strptime(data.get('issue_date'), '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(data.get('expiry_date'), '%Y-%m-%d').date(),
            signature=data.get('signature', ''),
            theme=data.get('theme', 'default'),
            photo_filename=photo_filename,
            logo_filename=logo_filename,
            background_filename=background_filename,
            font_family=data.get('font_family', 'DejaVuSans'),
            font_size=int(data.get('font_size', 10)),
            card_png=card_filename,
            card_pdf=pdf_filename,
            qr_code=os.path.basename(qr_path),
            template_id=template_id,
            status='VALID'
        )
        db.session.add(id_card)
        db.session.commit()
        
        add_audit_log('Card Generated', id_card.id, f"ID: {data.get('id_number')}")
        
        return jsonify({
            'success': True,
            'card_id': id_card.id,
            'card_png': card_filename,
            'card_pdf': pdf_filename
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify/<id_number>')
def verify_card(id_number):
    card = IDCard.query.filter_by(id_number=id_number).first()
    if not card:
        return render_template('verify.html', status='NOT_FOUND')
    
    # Check expiry
    if card.expiry_date < datetime.now().date():
        card.status = 'EXPIRED'
        db.session.commit()
    
    return render_template('verify.html', card=card)

@app.route('/settings')
def settings():
    cards = IDCard.query.order_by(IDCard.created_at.desc()).all()
    templates = CardTemplate.query.all()
    watermark = Watermark.query.first()
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
    return render_template('settings.html', cards=cards, templates=templates, watermark=watermark, logs=logs)

@app.route('/api/card/<int:card_id>/revoke', methods=['POST'])
def revoke_card(card_id):
    card = IDCard.query.get_or_404(card_id)
    card.status = 'REVOKED'
    db.session.commit()
    add_audit_log('Card Revoked', card.id, f"ID: {card.id_number}")
    return jsonify({'success': True})

@app.route('/api/card/<int:card_id>/enable', methods=['POST'])
def enable_card(card_id):
    card = IDCard.query.get_or_404(card_id)
    card.status = 'VALID'
    db.session.commit()
    add_audit_log('Card Enabled', card.id, f"ID: {card.id_number}")
    return jsonify({'success': True})

@app.route('/admin/card/<int:card_id>/view')
def view_card_admin(card_id):
    card = IDCard.query.get_or_404(card_id)
    return jsonify({
        'id_number': card.id_number,
        'full_name': card.full_name,
        'organization': card.organization,
        'date_of_birth': card.date_of_birth.strftime('%Y-%m-%d'),
        'status': card.status,
        'card_png': card.card_png
    })

@app.route('/api/watermark', methods=['POST'])
def update_watermark():
    data = request.json
    watermark = Watermark.query.first()
    if not watermark:
        watermark = Watermark()
    
    watermark.text = data.get('text', 'STAFF')
    watermark.color = data.get('color', '#888888')
    watermark.opacity = int(data.get('opacity', 128))
    watermark.position = data.get('position', 'center')
    watermark.enabled = data.get('enabled', True)
    
    db.session.add(watermark)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/template', methods=['POST'])
def save_template():
    data = request.json
    template_id = data.get('id')
    template = CardTemplate.query.filter_by(id=template_id).first() if template_id else None
    
    if not template:
        template = CardTemplate(name=data.get('name'))
    
    template.name = data.get('name')
    template.set_config(data.get('config', {}))
    template.is_active = data.get('is_active', True)
    
    db.session.add(template)
    db.session.commit()
    
    return jsonify({'success': True, 'template_id': template.id})

def init_db():
    with app.app_context():
        db.create_all()
        
        # Database migration: Check for missing columns
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('id_cards')]
        
        if 'logo_filename' not in columns:
            db.session.execute(db.text('ALTER TABLE id_cards ADD COLUMN logo_filename VARCHAR(255)'))
        if 'font_family' not in columns:
            db.session.execute(db.text('ALTER TABLE id_cards ADD COLUMN font_family VARCHAR(100)'))
        if 'font_size' not in columns:
            db.session.execute(db.text('ALTER TABLE id_cards ADD COLUMN font_size INTEGER'))
        if 'background_filename' not in columns:
            db.session.execute(db.text('ALTER TABLE id_cards ADD COLUMN background_filename VARCHAR(255)'))
        db.session.commit()
        
        # Delete old templates and create modern ones
        CardTemplate.query.delete()
        
        # Modern, professional ID card templates
        modern_templates = [
            {
                'name': 'Executive Elite',
                'config': {
                    'width': 640,
                    'height': 400,
                    'background_color': '#ffffff',
                    'header_height': 80,
                    'header_color': '#1a1f3a',
                    'photo_bg_color': '#f5f5f5',
                    'accent_color': '#0066cc',
                    'photo_x': 25,
                    'photo_y': 85,
                    'text_x': 200,
                    'text_y': 85,
                    'qr_x': 550,
                    'qr_y': 310,
                    'qr_size': 70,
                    'corner_radius': 8
                }
            },
            {
                'name': 'Minimalist Clean',
                'config': {
                    'width': 640,
                    'height': 400,
                    'background_color': '#f8f9fa',
                    'header_height': 60,
                    'header_color': '#ffffff',
                    'photo_bg_color': '#e9ecef',
                    'accent_color': '#495057',
                    'photo_x': 25,
                    'photo_y': 70,
                    'text_x': 200,
                    'text_y': 70,
                    'qr_x': 550,
                    'qr_y': 315,
                    'qr_size': 65,
                    'border_color': '#dee2e6',
                    'border_width': 2
                }
            },
            {
                'name': 'Corporate Blue',
                'config': {
                    'width': 640,
                    'height': 400,
                    'background_color': '#ffffff',
                    'header_height': 70,
                    'header_color': '#003d7a',
                    'photo_bg_color': '#e3f2fd',
                    'accent_color': '#0066cc',
                    'photo_x': 25,
                    'photo_y': 80,
                    'text_x': 200,
                    'text_y': 80,
                    'qr_x': 550,
                    'qr_y': 310,
                    'qr_size': 70,
                    'shadow': True
                }
            },
            {
                'name': 'Modern Gradient',
                'config': {
                    'width': 640,
                    'height': 400,
                    'background_color': '#ffffff',
                    'header_height': 75,
                    'header_color': '#667eea',
                    'photo_bg_color': '#f0f4ff',
                    'accent_color': '#667eea',
                    'secondary_accent': '#764ba2',
                    'photo_x': 25,
                    'photo_y': 85,
                    'text_x': 200,
                    'text_y': 85,
                    'qr_x': 550,
                    'qr_y': 310,
                    'qr_size': 70,
                    'gradient': True
                }
            },
            {
                'name': 'Professional Dark',
                'config': {
                    'width': 640,
                    'height': 400,
                    'background_color': '#ffffff',
                    'header_height': 70,
                    'header_color': '#2c3e50',
                    'photo_bg_color': '#ecf0f1',
                    'accent_color': '#34495e',
                    'photo_x': 25,
                    'photo_y': 80,
                    'text_x': 200,
                    'text_y': 80,
                    'qr_x': 550,
                    'qr_y': 310,
                    'qr_size': 70
                }
            },
            {
                'name': 'Tech Modern',
                'config': {
                    'width': 640,
                    'height': 400,
                    'background_color': '#0f1419',
                    'header_height': 70,
                    'header_color': '#1a1f3a',
                    'photo_bg_color': '#1e2536',
                    'accent_color': '#00d9ff',
                    'text_color': '#ffffff',
                    'photo_x': 25,
                    'photo_y': 80,
                    'text_x': 200,
                    'text_y': 80,
                    'qr_x': 550,
                    'qr_y': 310,
                    'qr_size': 70
                }
            }
        ]
        
        for tmpl in modern_templates:
            template = CardTemplate(name=tmpl['name'], is_active=True)
            template.set_config(tmpl['config'])
            db.session.add(template)
        
        # Create default watermark
        watermark = Watermark()
        db.session.add(watermark)
        
        db.session.commit()

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def cleanup_old_images():
    """Delete images older than 2 minutes from static folders"""
    with app.app_context():
        now = time.time()
        max_age = 120  # 2 minutes in seconds
        
        folders = [
            app.config['UPLOAD_FOLDER'],
            'static/qrcodes',
            'static/cards',
            'static/pdfs'
        ]
        
        for folder in folders:
            if not os.path.exists(folder):
                continue
                
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                # Skip .keep files or other important files if any
                if os.path.isfile(file_path):
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > max_age:
                        try:
                            os.remove(file_path)
                            print(f"Deleted old file: {file_path}")
                        except Exception as e:
                            print(f"Error deleting {file_path}: {e}")

if __name__ == '__main__':
    init_db()
    
    # Initialize and start scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_old_images, trigger="interval", seconds=60)
    scheduler.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
