# ⚡ SkillForge AI

> **Your AI-Powered Career Companion** — Upload your resume, discover skill gaps, and get a personalized learning roadmap powered by Google Gemini AI.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-green?logo=flask)
![Gemini](https://img.shields.io/badge/Google_Gemini-AI-orange?logo=google)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?logo=mysql)

---

## 🎯 Problem Statement

Job seekers struggle to identify skill gaps between their current abilities and dream job requirements. Traditional learning paths are generic and don't adapt to individual backgrounds.

## 💡 Solution

SkillForge AI uses **Google Gemini AI** to analyze your resume, identify skill gaps, and generate a fully personalized learning roadmap — complete with free resources, certifications, portfolio projects, and interview preparation.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **AI Resume Analysis** | Upload PDF resume → AI extracts skills automatically |
| 📊 **ATS Resume Score** | Get scored against Applicant Tracking Systems with improvement tips |
| 🗺️ **Smart Roadmaps** | AI-generated learning path with phases, topics, and free resources |
| 🎯 **Interview Prep** | Role-specific interview questions with model answers |
| 🤖 **AI Career Mentor** | Chat 24/7 with a personalized AI mentor |
| 📈 **Progress Analytics** | Track your learning journey with interactive charts |
| 🏆 **Certifications** | AI-recommended certifications for your career path |
| 💼 **Portfolio Projects** | Suggested projects to build for your target role |
| 🌙 **Dark/Light Mode** | Premium theme toggle for comfortable viewing |

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask (Blueprints)
- **AI Engine**: Google Gemini API (`gemini-3.5-flash`) with model fallback chain
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Deployment**: Railway / Render

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MySQL (XAMPP or standalone)
- Google Gemini API Key ([Get one free](https://aistudio.google.com/apikey))

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/SkillForge-AI.git
cd SkillForge-AI

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API key and MySQL credentials

# Start MySQL (XAMPP) then run:
python app.py
```

Visit **http://127.0.0.1:5000** 🎉

---

## 📁 Project Structure

```
SkillForge-AI/
├── app.py                 # Flask app factory
├── config.py              # Environment config
├── requirements.txt       # Python dependencies
├── models/
│   ├── db.py              # Database connection + schema
│   ├── user.py            # User CRUD operations
│   └── roadmap.py         # Roadmap CRUD operations
├── services/
│   ├── ai_engine.py       # Gemini AI integration (retry + fallback)
│   └── progress_service.py # Progress tracking logic
├── routes/
│   ├── auth_routes.py     # Login, Register, Logout, Demo Roadmaps
│   ├── dashboard_routes.py # Dashboard + Resume upload
│   ├── roadmap_routes.py  # Roadmap generation API
│   ├── api_routes.py      # REST API endpoints
│   ├── analytics_routes.py # Analytics page
│   └── chat_routes.py     # AI Mentor chat
├── templates/             # Jinja2 HTML templates
├── static/
│   ├── css/main.css       # Design system + themes
│   └── js/                # Frontend JavaScript
└── uploads/               # Uploaded resumes (gitignored)
```

---

## 🔑 Key Technical Highlights

- **AI Model Fallback Chain**: Automatically rotates between `gemini-3.5-flash` → `gemini-flash-latest` → `gemini-3.1-flash-lite` on quota/overload errors
- **3-Call Chained LLM Pipeline**: Industry profiling → Gap analysis → Roadmap generation
- **Public Demo Roadmaps**: View sample roadmaps without login at `/demo-roadmap/<role>`
- **MySQL Bytes Handling**: Proper conversion of MySQL boolean `bytes` type to Python `bool`

---

## 📄 License

Built for hackathon purposes. All rights reserved.

---

<p align="center">
  Built with ❤️ and AI for the next generation of professionals.
</p>
