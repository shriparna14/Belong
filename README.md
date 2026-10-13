# Belong — Campus Lost & Found Platform

A centralized campus lost-and-found platform that helps students report lost belongings, discover found items, verify ownership, and recover their belongings through a structured and secure process.

Built with Django, Belong brings together item reporting, public search, matching suggestions, ownership claims, supervised handovers, and administrative management.

---

## Table of Contents

- [Overview](#overview)
- [Objectives](#objectives)
- [Technology Stack](#technology-stack)
- [Key Features](#key-features)
- [System Workflow](#system-workflow)
- [Team Responsibilities](#team-responsibilities)
- [Project Structure](#project-structure)
- [Database Design](#database-design)
- [Installation and Setup](#installation-and-setup)
- [PostgreSQL Configuration](#postgresql-configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Security and Privacy](#security-and-privacy)
- [Future Enhancements](#future-enhancements)

---

## Overview

Lost belongings are a common problem in college and university campuses. Traditional reporting methods often rely on informal messages, notice boards, or disconnected communication channels, making it difficult to locate items and verify their ownership.

Belong provides a centralized platform where users can report lost and found items, search existing reports, discover potential matches, and submit ownership claims. The system also supports verification and supervised handover workflows to improve accountability when returning recovered belongings.

---

## Objectives

- Centralize lost-and-found reporting within the campus community.
- Provide secure user registration, authentication, and profile management.
- Enable users to create and manage lost and found reports.
- Improve item discovery through search, filters, and matching suggestions.
- Protect confidential ownership information from public access.
- Support ownership verification and supervised item handovers.
- Maintain relevant custody and handover records.
- Provide administrative tools for managing reports and claims.

---

## Technology Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python, Django |
| **Frontend** | HTML5, CSS3, JavaScript |
| **UI Framework** | Bootstrap 5 |
| **Database** | PostgreSQL |
| **Local Development Database** | SQLite, if enabled in configuration |
| **Authentication** | Django Authentication System |
| **Image Processing** | Pillow |
| **Environment Configuration** | python-dotenv |
| **PostgreSQL Driver** | psycopg2-binary |

Dependencies are managed through `requirements.txt`.

---

## Key Features

### 1. User Accounts and Item Reporting
- User registration, login, and logout.
- Profile viewing and editing.
- Django authentication and role-based access.
- Lost and found item reporting.
- Item and category models.
- Photograph upload and validation.
- Report creation and editing.
- Permission checks for report management.

### 2. Public Board, Search and Matching
- Public Lost & Found board.
- Item cards and detail pages.
- Keyword-based search.
- Category, location, and date filters.
- Matching suggestions between lost and found reports.
- Public listings that exclude confidential ownership details.
- Search results and item status indicators.

### 3. Claims, Handover and Administration
- Ownership claim submission and status tracking.
- Private ownership details and verification challenges.
- Claim review and decision management.
- Security personnel dashboard.
- Administrative dashboard and basic analytics.
- Supervised item handover using OTP or signature confirmation.
- Custody history and handover records.
- Item ageing and disposal management.

> *Feature availability should be verified against the current implementation and test results.*

---

## System Workflow

1. **Register and log in**: Users create accounts and access the platform.
2. **Report an item**: A user submits a lost or found report with relevant details and an optional photograph.
3. **Discover items**: Users browse the public board and search using keywords, categories, locations, and dates.
4. **Find potential matches**: The application suggests potentially matching lost and found reports.
5. **Submit a claim**: A user provides an ownership explanation and supporting evidence where required.
6. **Verify ownership**: An authorized reviewer evaluates the claim and verification details.
7. **Complete the handover**: The item is returned through the configured OTP or signature-based process.
8. **Maintain records**: Relevant custody, handover, ageing, and disposal information is recorded.

---

## Team Responsibilities

The project is divided into three parts, with each member responsible for the frontend, backend, and testing of their assigned module.

### Member 1 — User Accounts & Item Reporting (Part 1)

- **Frontend**:
  - Homepage and navigation.
  - Registration, login, and profile pages.
  - Lost and found reporting forms.
- **Backend**:
  - Django authentication and user roles.
  - Item and category models.
  - Photo upload and validation.
  - Saving and editing lost/found reports.
- **Testing**:
  - Authentication.
  - Permissions and authorization.
  - Item submission.
- **Deliverable**: A functional user-account and reporting module with appropriate validation, database integration, and access control.

### Member 2 — Public Board, Search & Matching (Part 2)

- **Frontend**:
  - Public Lost & Found board.
  - Item cards and detail pages.
  - Search, filters, and matching-results interface.
- **Backend**:
  - Campus location and category management.
  - Search by keyword, category, location, and date.
  - Matching suggestions between lost and found reports.
  - Public board responses with sensitive information removed.
- **Testing**:
  - Search accuracy.
  - Matching results.
  - Privacy of public responses.
- **Deliverable**: A public discovery module that helps users find relevant items while protecting confidential ownership information.

### Member 3 — Claims, Handover & Administration (Part 3)

- **Frontend**:
  - Claim and verification pages.
  - Security personnel dashboard.
  - Admin dashboard and basic analytics.
- **Backend**:
  - Claim submission and claim-status workflow.
  - Private ownership details and verification challenges.
  - Security-supervised handover with OTP or signature confirmation.
  - Custody history, ageing, and disposal records.
- **Testing**:
  - Claim verification.
  - Handover permissions.
  - Custody records.
  - Disposal workflow.
- **Deliverable**: A claim-management and verification module with supervised handover and administrative capabilities.

### Shared Responsibilities

All three members contribute to:
- Integration between Django apps and URL routes.
- Database schema coordination and migrations.
- Authentication, authorization, and privacy checks.
- Consistent UI and reusable templates.
- Integration testing and bug fixing.
- Version control, documentation, and final project validation.

---

## Project Structure

The following is a high-level representation matching the repository:

```text
Belong/
├── accounts/          # User accounts, authentication, profiles, and notifications
├── items/             # Item reports, categories, locations, and public board
├── claims/            # Claims, verification, and handover workflows
├── config/            # Django settings and root URL configuration
├── templates/         # HTML templates (Bootstrap 5 & custom components)
│   ├── accounts/
│   ├── claims/
│   ├── includes/
│   └── items/
├── static/
│   ├── css/           # Stylesheets (custom design system)
│   └── js/            # JavaScript utilities
├── media/             # Uploaded files at runtime (git-ignored)
├── requirements.txt   # Python project dependencies
├── .env.example       # Example environment configuration template
├── manage.py          # Django management script
└── README.md          # Project documentation
```

---

## Database Design

The main data entities include:

| Entity | Purpose |
| :--- | :--- |
| **User and Profile** | Account credentials, profile details, and user roles |
| **Category** | Classification of lost and found items |
| **Campus Location** | Campus buildings and reporting locations |
| **Item** | Item details, report type, photograph, location, reporter, and status |
| **Claim** | Claimant information, ownership explanation, evidence, and review status |
| **Verification Record** | OTP or signature-related verification information |
| **Handover Record** | Handover participants, timestamps, and relevant notes |
| **Ageing and Disposal Record** | Records associated with unclaimed items and disposal |

The schema follows the models implemented in the project. Existing models are reused rather than duplicating entities.

---

## Installation and Setup

### Prerequisites
- Python (compatible with the project's Django version)
- pip
- PostgreSQL (if running PostgreSQL)
- Git (if cloning the repository)

### 1. Clone the repository
```bash
git clone https://github.com/shriparna14/Belong.git
cd Belong
```
*If you already have the project locally, open its root directory instead.*

### 2. Create a virtual environment

**Windows PowerShell:**
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a local `.env` file using `.env.example` as a reference. Update the database and application settings for your environment:

```bash
cp .env.example .env
```

> **Warning:** Do not commit `.env` or real credentials to version control.

### 5. Apply database migrations
```bash
python manage.py migrate
```

### 6. Create an administrator account
```bash
python manage.py createsuperuser
```
Follow the prompts to create your administrator account.

### 7. Start the development server
```bash
python manage.py runserver
```
Open the application at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## PostgreSQL Configuration

If PostgreSQL is enabled in the Django settings, configure the corresponding database environment variables in `.env`:

```ini
DB_ENGINE=django.db.backends.postgresql
DB_NAME=belong_db
DB_USER=belong_user
DB_PASSWORD=your_local_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

Before running migrations:
1. Start PostgreSQL.
2. Create the database (`belong_db`) and database user.
3. Grant the required database permissions.
4. Set the correct values in `.env`.
5. Apply migrations:

```bash
python manage.py migrate
python manage.py check
python manage.py runserver
```

> **Note:** The environment-variable names must match those used in `config/settings.py`. Never publish actual passwords or secret keys.

---

## Running the Application

Common Django commands:

```bash
# Validate Django configuration
python manage.py check

# Apply migrations
python manage.py migrate

# Start the development server
python manage.py runserver

# Run automated tests
python manage.py test
```

---

## Testing

Testing covers the responsibilities of all three members:

### Member 1
- Registration, login, logout, and profile editing.
- Authentication and permission checks.
- Item submission and editing.
- Invalid form data and image uploads.
- Unauthorized report modifications.

### Member 2
- Search by keyword, category, location, and date.
- Search accuracy and combined filters.
- Matching suggestions.
- Privacy of public responses.
- Protection of confidential ownership information.

### Member 3
- Claim submission and status transitions.
- Ownership verification.
- Invalid or expired OTPs, if OTP is implemented.
- Signature confirmation, if implemented.
- Handover permissions.
- Custody records and ageing/disposal workflows.

### Integration
- Complete workflow from item reporting to recovery.
- Database migrations and PostgreSQL connectivity.
- Unauthorized access to restricted pages.
- Regression testing after integrating all modules.

Run the test suite using:
```bash
python manage.py test
```

*Record actual test results after execution. The presence of a feature in the source code does not, by itself, establish that it has passed testing.*

---

## Security and Privacy

- Keep secret keys and database credentials out of source control.
- Use Django authentication and server-side permission checks.
- Preserve CSRF protection on forms that modify data.
- Validate uploaded files and enforce file-size limits.
- Restrict report editing and deletion to authorized users.
- Exclude private ownership information from public responses.
- Protect claim details and verification challenges.
- Prevent unauthorized handovers.
- Test OTP expiry and reuse prevention when OTP verification is used.
- Configure HTTPS, secure cookies, allowed hosts, and production settings before deployment.
- Remove development credentials and sample data before public deployment.

---

## Future Enhancements

Potential enhancements include:
- More precise matching suggestions using item attributes.
- In-app notifications for claim-status updates.
- Improved accessibility and mobile usability.
- Expanded automated and end-to-end testing.
- Recovery-rate and item-ageing analytics.
- Production deployment documentation and secure media storage.

---

**Belong** — Helping campus communities find, verify, and recover lost belongings.
