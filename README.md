# AutoJobApply — Automated Job Application Portal

A professional, multi-user web portal that automatically applies to jobs using Playwright browser automation, PDF resume parsing, and a human-in-the-loop review step before submission.

---

## � Quick Start with Docker (Recommended)

The fastest way to get started is using Docker Compose:

```bash
# Copy environment file
cp .env.example .env

# Edit .env and set your MySQL password
# DB_PASSWORD=your_mysql_password_here

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

Services will be available at:
- **Frontend & API**: http://localhost:3000
- **Automation Service**: http://localhost:5001
- **MySQL**: localhost:3306

---

## 🛠️ Manual Setup

### 1. MySQL Database
1. Open **MySQL Workbench**
2. Connect to your local MySQL server
3. Open and run: `backend/models/db_schema.sql`
4. This creates the `autojobapply` database with all 5 tables.

### 2. Backend (Node.js)
```powershell
# Navigate to backend
cd backend

# Copy and edit .env file
cp .env.example .env
# Edit .env — set your MySQL password
# DB_PASSWORD=your_mysql_password_here

# Install dependencies
npm install

# Start server
npm start
```
The API runs on **http://localhost:3000**

### 3. Automation Service (Python)
```powershell
# Navigate to automation folder
cd automation

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Start service
python app.py
```
The automation service runs on **http://localhost:5001**

### 4. Open the App
Navigate to **http://localhost:3000** in your browser.

---

## 🚀 User Flow

1. **Register / Login** → Create your account
2. **Profile Wizard** → Upload PDF resume (auto-parsed) → Fill personal info, skills, work history, Q&A defaults
3. **Add Jobs** → Paste any carrier job URL on the Dashboard OR use Jobs board
4. **Apply** → Click Apply → System pre-fills all form fields from your profile
5. **Review** → Edit any field, answer Yes/No questions, update cover letter
6. **Confirm & Submit** → Playwright opens the real job site, fills the form, uploads your resume, and submits
7. **History** → Track all applications and their statuses

---

## 📁 Project Structure

```
AutoJobApply/
├── backend/
│   ├── server.js          ← Express entry point (port 3000)
│   ├── .env               ← ⚠️ Edit this with your DB password
│   ├── config/db.js       ← MySQL connection pool
│   ├── middleware/        ← JWT auth, file upload
│   ├── routes/            ← API routes (auth, profile, jobs, applications)
│   ├── controllers/       ← Business logic
│   ├── models/
│   │   └── db_schema.sql  ← Run this in MySQL Workbench first!
│   └── uploads/           ← Resumes and profile photos stored here
│
├── automation/
│   ├── app.py             ← Flask service (port 5001)
│   ├── form_filler.py     ← Playwright engine with retry logic
│   ├── job_searcher.py    ← Job search across multiple platforms
│   ├── logger_config.py   ← Structured logging configuration
│   ├── retry_utils.py     ← Exponential backoff retry logic
│   ├── config_validator.py ← Environment validation
│   └── requirements.txt
│
├── frontend/
│   ├── index.html         ← Login
│   ├── register.html
│   ├── dashboard.html
│   ├── profile.html       ← Step wizard
│   ├── jobs.html
│   ├── apply.html         ← ⭐ Review before submit
│   ├── history.html
│   ├── settings.html
│   ├── css/               ← main.css, theme.css, components.css
│   └── js/                ← api.js, auth.js, dashboard.js, profile.js, jobs.js, apply.js, history.js, settings.js, theme.js
│
├── docker-compose.yml    ← Docker orchestration
├── Dockerfile            ← Backend container
├── automation/Dockerfile  ← Automation service container
└── .env.example          ← Environment variables template
```

---

## ⚙️ Environment Variables

### Backend (.env)
| Variable | Description | Default |
|---|---|---|
| `PORT` | Backend port | 3000 |
| `DB_HOST` | MySQL host | localhost |
| `DB_PORT` | MySQL port | 3306 |
| `DB_USER` | MySQL username | root |
| `DB_PASSWORD` | ⚠️ **Set your MySQL password here** | - |
| `DB_NAME` | Database name | autojobapply |
| `JWT_SECRET` | Change this to a random string in production | - |
| `AUTOMATION_SERVICE_URL` | Python service URL | http://localhost:5001 |

### Automation Service
| Variable | Description | Default |
|---|---|---|
| `PORT` | Flask service port | 5001 |
| `FORM_AGENT_SERVICE_URL` | Form agent service URL | http://localhost:5006 |
| `AUTOJOBAPPLY_LOGIN_WAIT_SECONDS` | Login wait timeout | 600 |
| `AUTOJOBAPPLY_FIELD_REVIEW_TIMEOUT_SECONDS` | Field review timeout | 900 |
| `AUTOJOBAPPLY_PROFILE_DIR` | Browser profile directory | - |

---

## 🔧 Health Checks

### Automation Service
```bash
# Basic health check
curl http://localhost:5001/health

# Detailed health check with system info
curl http://localhost:5001/health/detailed
```

### Backend API
```bash
# API health check
curl http://localhost:3000/api/health
```

---

## 🎨 Design System

- **Theme**: Amazon-inspired dark/light mode with `#FF9900` orange accent
- **Font**: Inter (Google Fonts)
- **Dark mode default** — toggle in topbar or Settings page
- Fully responsive for desktop and tablet

---

## 🔒 Security & Reliability Improvements

- **Structured Logging**: All operations logged with timestamps and severity levels
- **Retry Logic**: Exponential backoff for network failures and timeouts
- **Error Handling**: Comprehensive error handling with detailed logging
- **Health Checks**: Endpoint monitoring for service availability
- **Environment Validation**: Configuration validation on startup
- **Docker Support**: Containerized deployment for consistency

---

## ⚠️ Important Notes

- The automation service uses **Playwright Chromium** — a real browser window opens during application submission
- Always **review the form before confirming** — the automation fills fields but you approve first
- Resume PDF parsing extracts skills, phone, experience years using pattern matching
- For sites with heavy anti-bot detection (LinkedIn, etc.), you may need to log in to those sites first in a separate browser tab
- Logs are stored in `automation/logs/` for debugging
- Browser profile is maintained in `browser_profile/` for session persistence

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :5001

# Kill process if needed
taskkill /PID <PID> /F
```

### Playwright Browser Issues
```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

### Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues
1. Verify MySQL is running
2. Check credentials in .env file
3. Ensure database schema is imported
4. Check MySQL port (default: 3306)
