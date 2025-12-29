from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class IDCard(db.Model):
    __tablename__ = 'id_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    id_number = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    organization = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    signature = db.Column(db.String(200))
    theme = db.Column(db.String(50), default='default')
    photo_filename = db.Column(db.String(255))
    card_png = db.Column(db.String(255))
    card_pdf = db.Column(db.String(255))
    status = db.Column(db.String(20), default='VALID')  # VALID, REVOKED, EXPIRED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    qr_code = db.Column(db.String(255))
    template_id = db.Column(db.Integer, db.ForeignKey('card_template.id'))
    template = db.relationship('CardTemplate', backref='cards')

class CardTemplate(db.Model):
    __tablename__ = 'card_template'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    config = db.Column(db.Text, nullable=False)  # JSON string
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_config(self):
        return json.loads(self.config)
    
    def set_config(self, config_dict):
        self.config = json.dumps(config_dict)

class Watermark(db.Model):
    __tablename__ = 'watermark'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), default='STAFF')
    color = db.Column(db.String(7), default='#888888')  # Hex color
    opacity = db.Column(db.Integer, default=128)  # 0-255
    position = db.Column(db.String(20), default='center')  # top, center, bottom
    enabled = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_user = db.Column(db.String(100), default='user')
    action = db.Column(db.String(200))
    card_id = db.Column(db.Integer, db.ForeignKey('id_cards.id'))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AdminUser(db.Model):
    __tablename__ = 'admin_user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
