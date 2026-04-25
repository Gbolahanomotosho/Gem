
# 💎 Gem – AI-Powered Educational Assistant

**Gem** is an intelligent educational assistant that leverages multiple AI providers to help students with learning, homework, and concept explanation. It functions like a smart tutor accessible via web interface.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-lightgrey)
![AI](https://img.shields.io/badge/AI-Multi_Provider-orange)
![Render](https://img.shields.io/badge/Render-Deployment-purple)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-AI Provider** | Switches between different AI backends for reliability |
| 📚 **Homework Help** | Explains concepts and solves problems step-by-step |
| 🧠 **Personalized Tutoring** | Adapts explanations to student's level |
| 📧 **Email Summaries** | Sends learning session recaps to students/parents |
| 💾 **Session Storage** | SQLite database saves all learning interactions |
| ☁️ **Cloud Ready** | Configured for Render deployment |

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| **Backend** | Python, Flask |
| **AI Integration** | Multi-provider API abstraction layer |
| **Database** | SQLite |
| **Frontend** | HTML, CSS (single-page interface) |
| **Utilities** | Email service (session reports) |
| **Deployment** | Render (`render.yaml`, `Procfile`) |

---

## 📂 Project Structure

```

Gem/
├── app.py                # Main Flask application
├── teacher.py            # AI tutoring logic & prompt engineering
├── ai_providers.py       # Multi-AI provider abstraction layer
├── database.py           # SQLite session storage
├── email_service.py      # Email report automation
├── requirements.txt      # Python dependencies
├── Procfile              # Gunicorn entry for Render
├── render.yaml           # Render deployment config
├── init.py           # Package initializer
└── index.html            # Web interface (single page)

```

---

## 🔧 Installation & Local Testing

```bash
# Clone the repository
git clone https://github.com/Gbolahanomotosho/Gem.git
cd Gem

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your AI provider API keys (if using external services)
export AI_API_KEY="your_key_here"

# Run the Flask application
python app.py

# Open your browser to http://127.0.0.1:5000
```

---

🧠 What I Built (My Contribution)

· Multi-AI provider abstraction layer – Write code once, use any AI backend
· Flask web application – Complete tutoring interface
· Prompt engineering – Crafted educational prompts for clear concept explanations
· Session database – Tracks user learning history for personalized revisits
· Email reporting – Summarizes sessions for accountability
· Production deployment – Configured for Render cloud platform

---

📈 Example Workflow

1. User asks a question via web interface (e.g., "Explain Newton's laws")
2. Gem routes to AI provider using abstraction layer
3. AI generates educational response tailored to student level
4. Response displayed with step-by-step explanation
5. Session saved to SQLite database
6. Optionally emailed to student/parent as learning record

---

🚧 Current Status & Planned Improvements

Component Status
Multi-AI provider routing ✅ Complete
Web interface ✅ Complete
Session storage ✅ Complete
Email summaries ✅ Complete
Render deployment ✅ Complete
Subject-specific modes (Math, Science, History) 🔄 Planned
Quiz generation 🔄 Planned
Progress tracking dashboard 🔄 Planned
German language support 🔄 Planned

---

🎓 Why This Matters for German Employers

This project demonstrates:

· ✅ AI integration skills – Abstracting multiple providers behind one interface
· ✅ Educational technology domain – Growing field in Germany (EdTech startups)
· ✅ Full-stack deployment – Flask, database, email, cloud ready
· ✅ Practical problem-solving – Helps students learn more effectively
· ✅ Clean architecture – Separation of concerns (providers, database, email)

---

📫 Contact & Visa Status

Omotosho Gbolahan Hammed

· GitHub: Gbolahanomotosho
· Email: hammedg621@gmail.com
· 🛂 German IT Specialist Visa Eligible – 7+ years IT experience. No degree recognition required.

---

📜 License

MIT License – free for academic and commercial use with attribution.
