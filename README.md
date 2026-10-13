# Belong — Campus Lost & Found System

A secure, modern, full-stack Django application designed for college and university campuses to report lost belongings, list found items, and safely verify physical handoffs using a 6-digit cryptographic OTP mechanism.

---

## 🌟 Key Features

1. **Lost & Found Item Workflow**
   - Separate, intuitive reporting flows for **Lost Items** (with priority search) and **Found Items**.
   - Categories covering Electronics, Campus IDs & Cards, Keys, Bags & Wallets, Books, Eyewear, and more.
   - Campus Building and Zone tracking (Library, Student Union, Labs, Sports Pavilion, Cafeteria).
   - Confidential Identifying Details (serial numbers, wallpaper pictures, hidden markings) visible only to the reporter and authorized campus desk officers to verify genuine claims.

2. **Secure OTP-Based Physical Handoff**
   - When a student files an ownership claim with evidence, the item reporter or campus desk reviews the proof.
   - Upon approval, a time-limited **6-digit cryptographic OTP** is generated for the claimant.
   - At the time of physical pickup/return, the finder or desk officer inputs the claimant's OTP in-person.
   - Validating the OTP atomically transitions the item to **Returned & Reunited**, logs an immutable **HandoffAuditRecord**, and marks the claim complete.

3. **30-Day Item Aging & Campus Desk Management Console**
   - Configurable aging threshold (`ITEM_AGING_DAYS_THRESHOLD=30`).
   - Automated aging flags highlight items unclaimed past 30 days.
   - Dedicated **Campus Lost & Found Desk** console (`/desk/`) for university safety officers to manage aged inventory, storage locker custody, and in-person handoffs.

4. **Campus Account System**
   - Optional restriction of user registration to institutional email domains via `CAMPUS_ALLOWED_EMAIL_DOMAIN` in `.env`.
   - Student/Faculty ID and department profiling.
   - User Activity Dashboard (`/auth/dashboard/`) tracking reported items, submitted claims, and incoming pickup requests.

5. **Modern, Responsive Design System**
   - Glassmorphic navigation bar with real-time statistics chips.
   - Live OTP countdown timer and one-click copy button.
   - Instant search with dynamic category, location, and aging filter chips.
   - High-contrast visual status pills (`Active`, `Claim In Review`, `Ready for Pickup`, `Returned`, `Archived`).

---

## 🛠️ Project Structure

```
Django_Project/
├── accounts/               # Campus user authentication, registration & profiles
│   ├── forms.py
│   ├── models.py           # UserProfile (roles, campus_id, department, phone)
│   ├── urls.py
│   └── views.py            # Login, registration, profile, activity dashboard
├── items/                  # Lost & Found listings, search & campus desk
│   ├── forms.py            # ItemForm with file size limit validation
│   ├── models.py           # Category, CampusLocation, Item (aging logic)
│   ├── context_processors.py # Global stats counters (active, lost, found, reunited)
│   ├── urls.py
│   ├── views.py            # Index feed, item detail, reporting, campus desk
│   └── management/commands/seed_demo_data.py # Seed realistic campus test data
├── claims/                 # Ownership claims & OTP verification
│   ├── forms.py            # ClaimForm, OTPVerificationForm
│   ├── models.py           # Claim, HandoffOTP, HandoffAuditLog
│   ├── urls.py
│   └── views.py            # Create claim, review claim, verify OTP, regenerate OTP
├── config/                 # Django project settings & root URLs
│   ├── settings.py         # Configured with python-dotenv & dual DB support
│   └── urls.py
├── static/
│   ├── css/style.css       # Complete modern CSS design system
│   └── js/main.js          # Interactive countdown, copy OTP, image preview
├── templates/              # Semantic HTML5 templates
│   ├── base.html
│   ├── includes/           # Navbar, footer, alerts
│   ├── accounts/
│   ├── items/
│   └── claims/
├── .env                    # Local environment settings (SQLite enabled by default)
├── .env.example
├── requirements.txt
└── manage.py
```

---

## 🚀 Getting Started

### 1. Prerequisites & Virtual Environment
The virtual environment is located at `venv/`. To activate:
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# or MSYS2/Bash:
source venv/bin/activate
```

### 2. Database Setup & Migrations
SQLite is configured by default in `.env` for zero-configuration local development.
To run migrations:
```powershell
python manage.py migrate
```

*(Note: To switch to PostgreSQL, set `DB_ENGINE=django.db.backends.postgresql` and adjust `DB_USER`/`DB_PASSWORD` in `.env`).*

### 3. Load Sample Demo Data
Run the custom seed command to populate campus categories, locations, realistic listings, and test users:
```powershell
python manage.py seed_demo_data
```

### 4. Demo Login Credentials

| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Desk Admin / Officer** | `admin` | `admin123` | `admin@campus.edu` |
| **Student (Claimant)** | `alex_rivera` | `password123` | `alex.rivera@campus.edu` |
| **Student (Finder)** | `sarah_chen` | `password123` | `sarah.chen@campus.edu` |

### 5. Run Local Development Server
```powershell
python manage.py runserver
```
Navigate to [http://localhost:8000](http://localhost:8000) in your web browser.

---

## 🧪 Running Automated Tests
Run the full test suite covering item reporting, aging calculations, and end-to-end OTP verification:
```powershell
python manage.py test
```
