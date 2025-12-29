# Universal ID Card Generator (Live System)

## Project Overview
A full-stack Flask web application for generating professional ID cards with customizable templates, QR code verification, PDF export, and admin management system.

## Key Features Implemented

### 1. Core ID Card Generation
- Generate ID cards for workers, students, staff with custom data
- **Auto-Generated ID Numbers** - Unique IDs in format: ID20251229XXXXX (timestamp-based)
- Support for multiple themes (default/blue, green, red, corporate)
- Photo upload (PNG, JPG, GIF)
- Theme selection
- Output as PNG image and PDF download
- **Live Card Preview** - Real-time preview updates as you fill the form
- **Machine-Readable Zone (MRZ)** - Professional barcode-like text at bottom of card
- **Professional Design** - Gradient header, accent colors, modern layout

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
  - **Cards Tab**: View all generated cards with modal preview, revoke/enable status, download PNG/PDF
  - **Watermark Tab**: Customize watermark (text, color, opacity, position)
  - **Templates Tab**: Create, edit, and manage card templates with interactive modal
  - **Audit Log**: Track all admin actions

### 5. Interactive Modals
- **Card Preview Modal**: Click "View" to see full card details and generated card image
- **Template Editor Modal**: Add/edit card templates with visual form controls for:
  - Card dimensions (width/height)
  - Colors (header, background)
  - Element positions (photo, text, QR code)
  - Size adjustments

### 6. Watermark System
- Customizable text, color (hex), opacity (0-255)
- Position options: top, center, bottom
- Enable/disable toggle
- Applied dynamically during card generation
- Default: "STAFF" watermark

### 7. Additional Features
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
1. **Page loads automatically** with a generated Unique ID Number (click "Generate" to get a different one)
2. **Fill the form** on the homepage - as you type, the **Live Preview** on the right updates in real-time
3. Enter required details:
   - Full name
   - Date of birth (auto-populated in preview)
   - Organization
   - Address
   - Issue and expiry dates
4. Optional: Add signature, select theme, upload photo
5. Select card template from dropdown
6. Click **Generate Card** to create your professional ID card
7. Download as PNG (high-quality) or PDF
8. Click **Generate Another** to create more cards

**Features:**
- ✓ ID numbers auto-generate with timestamp for uniqueness
- ✓ Each card includes Machine-Readable Zone (MRZ) at bottom
- ✓ Professional gradient header with accent colors
- ✓ Live preview shows real-time updates

### Verify a Card
- Use QR code on the card or navigate to `/verify/<id_number>`
- Public verification shows only essential info

### Admin Access
1. Navigate to `/admin/login`
2. Login with: `admin` / `admin123`
3. **Cards Tab**: 
   - Click **View** to see card details in a modal popup
   - Revoke or enable cards
   - Download PNG or PDF
   - Pagination for browsing many cards
4. **Templates Tab**:
   - Click **Add Template** to create a new template
   - Click **Edit** to modify existing template with modal editor
   - Control card layout, colors, and element positions
5. **Watermark Tab**: Customize how watermarks appear on generated cards
6. **Audit Log**: Track all admin actions with timestamps

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

## Card Design Features

### Visual Elements
- **Header**: Gradient background with golden accent border
- **Colors**: Accent colors (navy, dark blue) on labels for professional appearance
- **Typography**: Bold headers, clear text hierarchy
- **MRZ**: Machine-Readable Zone with check digit for authenticity
- **Professional Layout**: Organized sections for info, dates, and MRZ

### Technical Implementation
- Card dimensions configurable (default: 1000×600px)
- Auto-generated IDs with timestamp: ID20251229XXXXX
- MRZ format: 2 lines, 44 characters each (similar to passports)
- Check digit validation for MRZ lines
- Theme colors: Blue, Green, Red, Corporate

## Initial Setup
The database and default admin user are automatically initialized on first run.

## Production Deployment
Before deployment, change `SECRET_KEY` in app.py and use a production WSGI server (Gunicorn, uWSGI, etc.)
