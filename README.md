# 🚀 AutoJobApply — Automated Job Application Portal

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg?cacheSeconds=2592000)
![Node](https://img.shields.io/badge/Node.js-18.x-green.svg)
![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)
![Playwright](https://img.shields.io/badge/Playwright-Browser_Automation-orange.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue.svg)

> A powerful, multi-user web portal that automatically applies to jobs using Playwright browser automation. It features PDF resume parsing, automated form-filling, Naukri.com support, and a human-in-the-loop review system.

---

## ✨ Key Features

- 🤖 **Playwright Automation:** Uses real Chromium browsers to bypass bot detection and fill out complex job applications.
- 📄 **Smart Resume Parsing:** Automatically extracts skills, experience, and contact details from your uploaded PDF resume.
- 🎯 **Naukri.com Integration:** Supports custom scripts to easily apply to Naukri jobs (Fresher, Experienced, specific locations).
- ✈️ **Autopilot Mode:** Queue up multiple job links and let the system apply to them in the background while you sleep.
- 🧑‍💻 **Human-in-the-loop:** Review the pre-filled forms before the bot hits "Submit" to ensure 100% accuracy.
- 🎨 **Modern Dashboard:** Beautiful, responsive UI with Dark/Light mode support.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Frontend** | HTML, CSS, JS | Vanilla JS with responsive, modern UI components. |
| **Backend API** | Node.js, Express | Handles user auth, job queues, and API routing. |
| **Database** | MySQL | Stores user profiles, application history, and jobs. |
| **Automation** | Python, Playwright | Drives the browser, handles interactions and wait-states. |

---

## 💻 Local Setup (Using Docker - Recommended)

The fastest way to run the project locally is via Docker Compose.

```bash
# 1. Clone the repository
git clone https://github.com/bharatvyas0712/autoapply.git
cd autoapply

# 2. Setup Environment Variables
cp .env.example .env
# Edit .env and set your DB_PASSWORD=your_password_here

# 3. Start all services (Database, Backend, and Python Automation)
docker-compose up -d
```
🌐 The portal will be live at: **http://localhost:3000**

---

## ☁️ Free Cloud Deployment (Zero Cost Setup)

If you want to host this on the internet 24/7 for free, you can split the services to bypass RAM limits on free tiers (since Playwright needs 1GB+ RAM).

### 1. Database (Aiven.io)
- Create a free MySQL database on [Aiven.io](https://aiven.io/).
- Copy your connection details (Host, Port, User, Password).

### 2. Backend (Render.com)
- Go to [Render](https://render.com/), create a **Web Service**, and connect this GitHub repo.
- Select `backend` as the root directory.
- Set Build command to `npm install` and Start command to `npm start`.
- Add your Database connection details in Render's Environment Variables.

### 3. Automation Worker (Local Machine)
Since free cloud servers only provide 512MB RAM, Playwright will crash. Run the worker locally to handle the heavy lifting:
```bash
cd automation
pip install -r requirements.txt
playwright install chromium
```
Update your `automation/.env` to point to your Render Backend:
`BACKEND_API_URL=https://your-render-url.onrender.com`

Run the worker: `python app.py`

---

## 📂 Project Structure

```text
AutoJobApply/
├── backend/               # Node.js API, JWT Auth, Database logic
├── automation/            # Python Playwright scripts, job_searcher.py
├── frontend/              # User Interface (Dashboard, Apply, Autopilot)
├── browser_profile/       # Stores browser session (cookies, logins)
├── docker-compose.yml     # Orchestration for local setup
└── Dockerfile             # Container configuration
```

---

## 📝 Important Notes

- **Browser Sessions:** The system saves cookies in `browser_profile/` so you don't have to log into job portals (like LinkedIn or Naukri) every single time.
- **Bot Detection:** If a site detects the bot, you may need to manually log in once using the non-headless browser mode.
- **Autopilot:** Leave your computer running while Autopilot processes your job queue!

---
*Made with ❤️ to make job hunting effortless.*
