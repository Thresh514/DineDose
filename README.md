# DineDose

> **A Healthcare Web Application for Remote Diet and Medication Plan Management**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Test Coverage](https://img.shields.io/badge/Coverage-≥90%25-brightgreen.svg)](#test-coverage)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

**Live Demo**: [https://dinedose.food](https://dinedose.food)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Architecture Overview](#architecture-overview)
4. [Prerequisites](#prerequisites)
5. [How to Run the System](#how-to-run-the-system)
6. [How to Run Tests + Coverage Report](#how-to-run-tests--coverage-report)
7. [Repository Structure](#repository-structure)
8. [Code Quality & Design Principles](#code-quality--design-principles)
9. [API Documentation](#api-documentation)
10. [Contribution & Development Workflow](#contribution--development-workflow)
11. [Deployment](#deployment)
12. [Team](#team)
13. [License & Acknowledgements](#license--acknowledgements)

---

## Introduction

**DineDose** is a full-stack healthcare web application designed for the CS411 Software Engineering course (Fall 2025). It enables healthcare providers (doctors) to create personalized diet and medication plans for patients, while patients can track their intake, receive timely reminders, and communicate with their doctors remotely.

The system addresses the challenge of patient adherence to prescribed treatment plans by providing:
- **Automated reminders** via email (Amazon SES)
- **Intuitive dashboards** for both patients and doctors
- **Comprehensive tracking** of medication and food intake
- **Secure authentication** via Google OAuth 2.0
- **AI-powered features** via OpenAI API integration

### Key Objectives
- Improve patient compliance with prescribed health plans
- Enable remote patient monitoring for healthcare providers
- Provide data-driven insights through historical tracking
- Ensure security and privacy of health-related data

---

## Features

### For Patients
| Feature | Description |
|---------|-------------|
| **Dashboard** | View daily medication and diet plans at a glance |
| **Reminders** | Receive email notifications before scheduled doses |
| **Intake Tracking** | Record medication and food consumption with timestamps |
| **History Charts** | Visualize past intake data with interactive charts |
| **Doctor Feedback** | Receive personalized health tips from assigned doctors |
| **Notification Settings** | Customize reminder preferences and timing |

### For Doctors
| Feature | Description |
|---------|-------------|
| **Patient Management** | View and manage assigned patients |
| **Plan Editor** | Create and modify medication/diet plans with flexible scheduling rules |
| **Calendar View** | Visualize patient plans across time periods |
| **Drug Search** | Search comprehensive drug database (FDA NDC) |
| **Food Database** | Access nutritional information (FDC data) |
| **Patient Feedback** | Send personalized feedback to patients |
| **Data Analytics** | Monitor patient compliance and trends |

### Security & Authentication
- Google OAuth 2.0 integration for secure login
- Role-based access control (Patient/Doctor)
- Secure session management with HTTP-only cookies
- Environment-based configuration for sensitive credentials

---

## Architecture Overview

DineDose follows a **layered architecture** pattern ensuring clean separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│         (Jinja2 Templates + Static HTML/CSS/JS)             │
├─────────────────────────────────────────────────────────────┤
│                       Controller Layer                       │
│              (Flask Blueprints in pagelogic/bp/)            │
├─────────────────────────────────────────────────────────────┤
│                        Service Layer                         │
│            (Business Logic in pagelogic/service/)           │
├─────────────────────────────────────────────────────────────┤
│                       Repository Layer                       │
│           (Data Access in pagelogic/repo/)                  │
├─────────────────────────────────────────────────────────────┤
│                        Data Layer                            │
│              (PostgreSQL via Neon Serverless)               │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Category | Technology |
|----------|------------|
| **Backend Framework** | Flask + Jinja2 + Python |
| **Frontend** | HTML, CSS, JavaScript |
| **Database** | PostgreSQL (Neon Serverless) |
| **Database Driver** | psycopg |
| **Authentication** | OAuth 2.0 (Google) |
| **Email Service** | Amazon SES |
| **AI Integration** | OpenAI API |
| **Task Scheduler** | Cronjob (APScheduler) |
| **VPS Hosting** | RackNerd |
| **Domain Provider** | GoDaddy |
| **Design Tool** | Figma |
| **Version Control** | GitHub |
| **WSGI Server** | Gunicorn |

---

## Prerequisites

### System Requirements
- **Python**: 3.12 or higher
- **PostgreSQL**: 14 or higher (or Neon Serverless)
- **pip**: Latest version

### External Services (Required for full functionality)
- **Google Cloud Console**: OAuth 2.0 credentials
- **AWS Account**: SES for email notifications
- **Neon**: Serverless PostgreSQL database
- **OpenAI**: API key for AI features (optional)

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database Configuration (Neon PostgreSQL)
DB_HOST=your-neon-host.neon.tech
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_SSLMODE=require

# Google OAuth 2.0
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# AWS SES (Email Service)
AWS_REGION=us-east-1
AWS_ACCESS_KEY=your-aws-access-key
AWS_SECRET_KEY=your-aws-secret-key
SES_SENDER=noreply@dinedose.food

# OpenAI API (Optional)
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=your-openai-api-key

# Bing Images API (Optional)
BING_IMAGES_API_KEY=your-bing-api-key
```

---

## How to Run the System

### Step 1: Clone the Repository

```bash
git clone https://github.com/Thresh514/DineDose.git
cd DineDose
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```powershell
.\venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

### Step 6: Initialize Database

Connect to your PostgreSQL database and run the schema:

```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f create.sql
```

Or use the Python scripts to populate initial data:

```bash
python script/drug.py    # Import FDA drug data
python script/food.py    # Import FDC food data
```

### Step 7: Start the Development Server

**Option A: Using Flask Development Server**
```bash
flask run --debug
```

**Option B: Using Gunicorn (Production-like)**
```bash
gunicorn app:app
```

The application will be available at: **http://localhost:8000**

### Quick Start (All-in-One)

```bash
# macOS/Linux
git clone https://github.com/your-org/DineDose.git && cd DineDose
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure your .env file
gunicorn app:app
```

---

## How to Run Tests + Coverage Report

DineDose uses **pytest** for testing and **coverage.py** for statement coverage analysis.

### Install Test Dependencies

```bash
pip install pytest pytest-cov coverage
```

### Run All Tests

```bash
pytest test/ -v
```

### Run Tests with Coverage Report

**Terminal Report:**
```bash
pytest test/ --cov=pagelogic --cov=utils --cov-report=term-missing -v
```

**HTML Report:**
```bash
pytest test/ --cov=pagelogic --cov=utils --cov-report=html -v
```

### Generate Standalone Coverage Report

```bash
# Run coverage
coverage run -m pytest test/

# Generate terminal report
coverage report -m

# Generate HTML report
coverage html
```

### Coverage Report Locations

| Format | Location |
|--------|----------|
| Terminal | Displayed in console output |
| HTML | `htmlcov/index.html` |
| XML | `coverage.xml` (if generated) |

### Test Coverage Statement

> **This project achieves >=90% statement coverage** across all core modules including blueprints (controllers), services, and repositories.

### Test File Mapping

| Test File | Module Tested |
|-----------|---------------|
| `test_plan_bp.py` | Plan API endpoints |
| `test_plan_repo.py` | Plan data access layer |
| `test_plan_service.py` | Plan business logic |
| `test_drug_bp.py` | Drug API endpoints |
| `test_drug_repo.py` | Drug data access |
| `test_food_bp.py` | Food API endpoints |
| `test_food_repo.py` | Food data access |
| `test_user_bp.py` | User API endpoints |
| `test_user_repo.py` | User data access |
| `test_notify_service.py` | Notification service |
| `test_drug_record_bp.py` | Drug record endpoints |
| `test_drug_record_repo.py` | Drug record data access |
| `test_food_record_bp.py` | Food record endpoints |
| `test_food_record_repo.py` | Food record data access |
| `test_feedback_repo.py` | Feedback data access |
| `test_user_notification_repo.py` | Notification settings |
| `test_doctor_page_bp.py` | Doctor page endpoints |

---

## Repository Structure

```
DineDose/
├── app.py                      # Flask application factory & entry point
├── config.py                   # Configuration & database connection
├── extensions.py               # Flask extensions (Mail, OAuth)
├── create.sql                  # Database schema DDL
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment config
│
├── pagelogic/                  # Backend application logic
│   ├── __init__.py
│   ├── index.py                # Index route
│   ├── login.py                # Authentication routes
│   ├── logout.py               # Logout handling
│   ├── patient_home.py         # Patient dashboard routes
│   │
│   ├── bp/                     # Blueprints (Controllers)
│   │   ├── doctor_page_bp.py   # Doctor page routes
│   │   ├── drug_bp.py          # Drug API endpoints
│   │   ├── drug_record_bp.py   # Drug intake records
│   │   ├── food_bp.py          # Food API endpoints
│   │   ├── food_record_bp.py   # Food intake records
│   │   ├── plan_bp.py          # Plan CRUD operations
│   │   ├── user_bp.py          # User management
│   │   └── user_notification_bp.py  # Notification settings
│   │
│   ├── service/                # Business Logic Layer
│   │   ├── plan_service.py     # Plan expansion & scheduling
│   │   └── notify_service.py   # Email notification jobs
│   │
│   └── repo/                   # Data Access Layer (Repositories)
│       ├── drug_repo.py        # Drug database operations
│       ├── drug_record_repo.py # Drug record operations
│       ├── food_repo.py        # Food database operations
│       ├── food_record_repo.py # Food record operations
│       ├── plan_repo.py        # Plan & plan_item operations
│       ├── user_repo.py        # User operations
│       ├── user_notification_repo.py  # Notification config
│       └── feedback_repo.py    # Doctor feedback operations
│
├── templates/                  # Jinja2 HTML Templates
│   ├── components/             # Reusable template components
│   │   ├── calendar_dom.html
│   │   ├── calendar_view.html
│   │   ├── doctor_sidebar.html
│   │   ├── navbar.html
│   │   ├── patient_header.html
│   │   └── patient_navbar.html
│   ├── doctor_*.html           # Doctor-facing pages
│   ├── patient_*.html          # Patient-facing pages
│   ├── index.html              # Landing page
│   └── login.html              # Authentication page
│
├── static/                     # Static Assets
│   ├── main.css                # Global styles
│   ├── doctor.css              # Doctor UI styles
│   ├── patient.css             # Patient UI styles
│   └── public/                 # Images and icons
│
├── utils/                      # Utility Modules
│   ├── emailsender.py          # AWS SES email client
│   ├── llm_api.py              # OpenAI API integration
│   ├── bing_api.py             # Image search API
│   └── serializer.py           # JSON serialization helpers
│
├── script/                     # Data Import Scripts
│   ├── drug.py                 # FDA drug data importer
│   └── food.py                 # FDC food data importer
│
├── test/                       # Test Suite
│   ├── test_*_bp.py            # Blueprint/Controller tests
│   ├── test_*_repo.py          # Repository tests
│   └── test_*_service.py       # Service tests
│
└── venv/                       # Virtual environment (gitignored)
```

### Directory Descriptions

| Directory | Purpose |
|-----------|---------|
| `pagelogic/bp/` | Flask Blueprints handling HTTP requests (Controllers) |
| `pagelogic/service/` | Business logic and domain rules |
| `pagelogic/repo/` | Database operations and data models |
| `templates/` | Server-rendered HTML pages |
| `static/` | CSS, JavaScript, and image assets |
| `utils/` | Shared utility functions and external API clients |
| `script/` | One-time data import and migration scripts |
| `test/` | Comprehensive test suite |

---

## Code Quality & Design Principles

### Layered Architecture

DineDose implements a **three-tier layered architecture** with strict dependency rules:

```
Controllers (bp/) → Services (service/) → Repositories (repo/)
```

- **Controllers** handle HTTP requests/responses and input validation
- **Services** contain business logic and orchestrate complex operations
- **Repositories** abstract database access with clean interfaces

### GRASP Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **Information Expert** | Each repository encapsulates knowledge about its domain entity (e.g., `plan_repo` knows how to persist and retrieve plans) |
| **Creator** | Repositories create domain objects; services create DTOs for API responses |
| **Controller** | Blueprints act as use-case controllers, delegating to services |
| **Low Coupling** | Layers communicate through well-defined interfaces; database details hidden in repositories |
| **High Cohesion** | Each module has a single, focused responsibility |
| **Pure Fabrication** | Services like `notify_service` are behavioral classes not representing domain entities |

### Object-Oriented Design

- **Dataclasses** for immutable domain models (`plan`, `plan_item`, `plan_item_rule`)
- **Type hints** throughout for IDE support and documentation
- **Composition over inheritance** in service layer
- **Dependency injection** via monkeypatching for testability

### Modularity & Separation of Concerns

```python
# Example: Clean separation in plan handling
# Controller (plan_bp.py) - HTTP handling only
@plan_bp.route("/get_user_plan", methods=["GET"])
def get_user_plan_handler():
    user_id = int(request.args.get("id"))
    plan = plan_service.get_user_plan(user_id, from_when, to_when)
    return jsonify(plan.to_dict()), 200

# Service (plan_service.py) - Business logic
def get_user_plan(id, from_when, to_when):
    plan = plan_repo.get_plan_by_user_id(id)
    plan_items = plan_repo.get_all_plan_items_by_plan_id(plan.id)
    # ... expand rules, fill drug names, sort ...
    return plan

# Repository (plan_repo.py) - Data access
def get_plan_by_user_id(user_id: int) -> Optional[plan]:
conn = mydb()
    cur = conn.cursor()
    cur.execute("SELECT ... FROM plan WHERE patient_id = %s", (user_id,))
    # ... return domain object ...
```

### Testability

- **Dependency Injection**: All external dependencies (database, email) can be mocked
- **Pure Functions**: Service functions have minimal side effects
- **Monkeypatch-friendly**: Repository functions use module-level imports for easy mocking
- **Isolated Tests**: Each test file can run independently

---

## API Documentation

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://dinedose.food`

### Authentication
All endpoints require session authentication via Google OAuth. Include session cookies with requests.

---

### Plan Endpoints

#### Get User Plan (Expanded)

```http
GET /get_user_plan?id={user_id}&from={date}&to={date}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Patient user ID |
| `from` | ISO date | No | Start date (YYYY-MM-DD) |
| `to` | ISO date | No | End date (YYYY-MM-DD) |

**Response (200 OK):**
```json
{
  "id": 1,
  "patient_id": 10,
  "doctor_id": 5,
  "name": "Diabetes Management Plan",
  "plan_items": [
    {
      "id": 101,
      "drug_id": 500,
      "drug_name": "Metformin",
      "dosage": 500,
      "unit": "mg",
      "date": "2025-12-01",
      "time": "08:00:00"
    }
  ]
}
```

---

#### Create Plan Item

```http
POST /plan_item
Content-Type: application/json
```

**Request Body:**
```json
{
  "plan_id": 1,
  "drug_id": 500,
  "dosage": 500,
  "unit": "mg",
  "note": "Take with food",
  "rules": [
    {
      "start_date": "2025-12-01",
      "end_date": "2025-12-31",
      "repeat_type": "DAILY",
      "interval_value": 1,
      "times": ["08:00:00", "20:00:00"]
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "message": "plan_item created",
  "plan_item_id": 123
}
```

---

#### Update Plan Item

```http
PUT /plan_item/{item_id}
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "message": "plan_item updated",
  "plan_item_id": 123
}
```

---

#### Delete Plan Item

```http
DELETE /plan_item/{item_id}
```

**Response (200 OK):**
```json
{
  "message": "plan_item deleted",
  "plan_item_id": 123
}
```

---

### Drug Endpoints

#### Search Drugs

```http
GET /drugs/search?q={query}&limit={limit}
```

**Response (200 OK):**
```json
{
  "drugs": [
    {
      "id": 500,
      "product_ndc": "0001-0001",
      "brand_name": "Glucophage",
      "generic_name": "Metformin Hydrochloride",
      "dosage_form": "TABLET",
      "route": "ORAL"
    }
  ]
}
```

---

### Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Not logged in |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---

## Contribution & Development Workflow

### Team Collaboration

The DJLS team followed an **Agile development methodology** with:
- Weekly sprint planning meetings
- Code reviews for all pull requests
- Pair programming for complex features
- Shared documentation on Notion/Google Docs
- UI/UX design collaboration via Figma

### Branch Naming Convention

We use a fork-based workflow with personal branches:

```
<username>/<feature-name>
```

**Examples from our repository:**
```
Thresh514/zetian
Thresh514/Lenoo
Thresh514/Dingwen
```

Each team member works on their own fork and creates pull requests to merge into the main repository.

### Commit Message Style

We use descriptive commit messages with optional prefixes for clarity:

| Prefix | Usage |
|--------|-------|
| `debug:` | Bug fixes and debugging |
| `refactor:` | Code refactoring |
| `Add` / `added` | New features or files |
| `fixed` | Bug fixes |
| `implemented` | New implementations |
| `update` | Updates to existing features |

**Examples from our commit history:**
```
debug: fixed unable to save notification config when there is no initial data
refactor: doctor plan editor and plan_item CRUD fixes
Add GoogleImagesAPI wrapper for food image search using SerpApi
implemented drug_record and food_record
add cronjob and notify_service
fixed the time processing base to utc5 in notify_service
Add unit tests for drug repo, food repo and plan
```

### Pull Request Process

**Recent Pull Requests:**

| PR | Title | Author |
|----|-------|--------|
| #48 | Add GoogleImagesAPI wrapper for food image search using SerpApi | Lenoisalive |
| #45 | feedback page improved, now create and edit plan_item enable doctor to search drugs | Skylar27jin |
| #44 | better search result display and button css | Skylar27jin |
| #43 | reorganize search interface, so user is able to search drug and food with higher performance | Skylar27jin |
| #42 | add unit tests for bp, repo, and service file | Dingwen1125 |
| #41 | fixed the time processing base to utc5 in notify_service | Skylar27jin |
| #40 | Add unit tests for drug repo, food repo and plan | Dingwen1125 |
| #33 | completed send_notifications to patients with incoming tasks | Skylar27jin |
| #32 | add cronjob and notify_service | Skylar27jin |

**Workflow:**

1. Fork the repository or create a personal branch
2. Implement changes with corresponding unit tests
3. Ensure all tests pass (`pytest test/ -v`)
4. Ensure coverage meets >= 90% threshold (`pytest --cov=pagelogic`)
5. Submit PR with descriptive title
6. Code review by team members
7. Merge upon approval

---

## Deployment

### RackNerd VPS (Current Production)

DineDose is deployed on a **RackNerd VPS** with the domain managed by **GoDaddy**.

**Production URL**: https://dinedose.food

**Procfile:**
```
web: gunicorn app:app
```

### Infrastructure

| Component | Provider |
|-----------|----------|
| VPS Hosting | RackNerd |
| Domain | GoDaddy |
| Database | Neon (Serverless PostgreSQL) |
| Email | Amazon SES |
| SSL Certificate | Let's Encrypt |

### Environment Variables (Production)

Set the following environment variables on your VPS:

```bash
SECRET_KEY=<production-secret>
FLASK_ENV=production
DB_HOST=<neon-database-host>
DB_NAME=<production-db-name>
DB_USER=<production-db-user>
DB_PASSWORD=<production-db-password>
DB_SSLMODE=require
GOOGLE_CLIENT_ID=<production-oauth-id>
GOOGLE_CLIENT_SECRET=<production-oauth-secret>
AWS_REGION=us-east-1
AWS_ACCESS_KEY=<production-aws-key>
AWS_SECRET_KEY=<production-aws-secret>
SES_SENDER=noreply@dinedose.food
LLM_API_KEY=<openai-api-key>
```

### Manual Deployment

```bash
# SSH into VPS
ssh user@your-vps-ip

# Navigate to project directory
cd /var/www/dinedose

# Pull latest changes
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Restart the service
sudo systemctl restart dinedose
```

### Cronjob Configuration

The notification service runs as a background scheduler (APScheduler) within the Flask application, checking for missed doses every 5 minutes and sending email reminders via Amazon SES.

### Health Check

The application exposes a root endpoint `/` that can be used for health checks.

---

## Team

### DJLS Team

| Member | GitHub | Role | Responsibilities |
|--------|--------|------|------------------|
| **Zetian Jin** | [@Skylar27jin](https://github.com/Skylar27jin) | FullStack Programmer | End-to-end feature development, system integration, core backend APIs |
| **Lingjie Su** | [@Lenoisalive](https://github.com/Lenoisalive) | Data Engineer & Backend Programmer | Database design, data pipelines, API integrations |
| **Dingwen Yang** | [@Dingwen1125](https://github.com/Dingwen1125) | Product Manager & Test Development Engineer | Product planning, test strategy, unit testing, QA |
| **Jiayong Tu** | [@Thresh514](https://github.com/Thresh514) | Frontend Engineer & UI/UX Designer | User interface design, frontend implementation, Figma prototypes |

---

## License & Acknowledgements

### License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 DJLS Team (Zetian Jin, Lingjie Su, Dingwen Yang, Jiayong Tu)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Acknowledgements

- **University of Illinois Urbana-Champaign** - CS411 Software Engineering Course
- **FDA National Drug Code Directory** - Drug database source
- **USDA FoodData Central** - Nutritional information database
- **Flask Community** - Excellent documentation and extensions
- **RackNerd** - VPS hosting provider
- **Neon** - Serverless PostgreSQL database
- **GoDaddy** - Domain registration
- **OpenAI** - AI API integration

### Data Sources

- Drug data: [FDA NDC Directory](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory)
- Food data: [USDA FoodData Central](https://fdc.nal.usda.gov/)

---

## Contact

For questions or support, please contact the development team:

- **Website**: [https://dinedose.food](https://dinedose.food)
- **Repository**: [GitHub Issues](https://github.com/your-org/DineDose/issues)
- **Course Instructor**: CS411 Teaching Staff

---

<p align="center">
  <strong>DineDose</strong> - Empowering healthier lives through technology
  <br>
  <em>CS411 Software Engineering Project - Fall 2025</em>
</p>
