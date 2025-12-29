# Universal ID Card Generator (Live System)

## Project Overview
A full-stack Flask web application for generating professional ID cards with customizable templates, QR code verification, PDF export, and admin management system.

## Key Features Implemented

### 1. Core ID Card Generation
- Generate ID cards for workers, students, staff with custom data
- Support for multiple themes (default/blue, green, red, corporate)
- Photo upload (PNG, JPG, GIF)
- Theme selection
- Output as PNG image and PDF download

### 2. Card Templates (Database-Driven)
- Default template with configurable dimensions
- Template storage in SQLite (JSON-based config)
- Admin can create and edit templates without code changes
- Template selection during card generation

### 3. QR Code Verification
- Automatic QR code generation on each card
- QR links to `/verify/<id_number>`
- Public verification page shows only:
  - Name
  - Organization
  - Status (VALID/REVOKED/EXPIRED)
  - Expiry date
- Sensitive data hidden from public access

### 4. Admin System
- Admin login/logout with hashed passwords
- Default credentials: username `admin`, password `admin123`
- Dashboard with tabs for:
  - **Cards Tab**: View all generated cards, revoke/enable status, download PNG/PDF
  - **Watermark Tab**: Customize watermark (text, color, opacity, position)
  - **Templates Tab**: Manage card templates
  - **Audit Log**: Track all admin actions

### 5. Watermark System
- Customizable text, color (hex), opacity (0-255)
- Position options: top, center, bottom
- Enable/disable toggle
- Applied dynamically during card generation
- Default: "STAFF" watermark

### 6. Additional Features
- Audit logging for admin actions
- Card status management (VALID/REVOKED/EXPIRED)
- Automatic expiry detection
- Pagination in admin dashboard
- Responsive design

## Tech Stack
- **Backend**: Flask 3.0.0
- **Database**: SQLite with SQLAlchemy ORM
- **Image Generation**: Pillow (PIL)
- **QR Codes**: qrcode
- **PDF Export**: ReportLab
- **Frontend**: HTML/CSS/Vanilla JavaScript
- **Security**: Werkzeug password hashing

## Database Schema
- **id_cards**: Stores generated ID card data
- **card_template**: Customizable card templates with JSON configs
- **watermark**: Watermark settings
- **audit_log**: Admin action history
- **admin_user**: Admin credentials

## How to Use

### Generate an ID Card
1. Fill the form on the homepage with:
   - Full name
   - Date of birth
   - Unique ID number
   - Organization
   - Address
   - Issue and expiry dates
   - Optional: signature, theme, photo upload
2. Select card template
3. Click "Generate Card"
4. Download as PNG or PDF

### Verify a Card
- Use QR code on the card or navigate to `/verify/<id_number>`
- Public verification shows only essential info

### Admin Access
1. Navigate to `/admin/login`
2. Login with: `admin` / `admin123`
3. Manage cards, customize watermarks, edit templates, view audit logs

## File Structure
```
/
├── app.py                    # Main Flask application
├── models.py                 # SQLAlchemy models
├── requirements.txt          # Python dependencies
├── utils/
│   ├── card_generator.py    # Card image generation
│   ├── qr_utils.py          # QR code generation
│   ├── pdf_export.py        # PDF export functionality
│   └── __init__.py
├── templates/
│   ├── index.html           # Homepage with card generator form
│   ├── login.html           # Admin login page
│   ├── dashboard.html       # Admin dashboard
│   ├── verify.html          # Public verification page
│   └── result.html          # Card result display
├── static/
│   ├── css/
│   │   └── style.css        # Global styles
│   ├── uploads/             # Uploaded photos
│   ├── cards/               # Generated PNG cards
│   ├── pdfs/                # Generated PDFs
│   └── qrcodes/             # Generated QR codes
└── idcards.db              # SQLite database (auto-created)
```

## Security Notes
- Passwords hashed with Werkzeug security
- Admin session-based authentication
- QR verification page never shows sensitive data
- File upload restricted to images only
- Max upload: 16MB

## Running the Application
```bash
python app.py
```
The app runs on `http://0.0.0.0:5000`

## Initial Setup
The database and default admin user are automatically initialized on first run.

## Production Deployment
Before deployment, change `SECRET_KEY` in app.py and use a production WSGI server (Gunicorn, uWSGI, etc.)
