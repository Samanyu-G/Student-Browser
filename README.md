# Student-Browser
📚 Student Productivity Suite

A hybrid Flask + PyQt5 Productivity App that includes:

✔ Pomodoro Timer

✔ To-Do List (SQLite)

✔ Study Statistics + Modern Graphs

✔ A Chromium-based Study Browser (PyQt WebEngine)

✔ Automatic Blocking of Distracting Websites during Study Mode

✔ Google Search enabled

🚀 Features
🔹 Flask Web Dashboard

Pomodoro timer

Add / mark / delete To-Do tasks

View total study time, average time, sessions completed

Visual graph of daily study minutes

Button to launch the Study Browser

🔹 PyQt5 Study Browser

Google homepage

Full navigation bar

Website blocking during study mode:

Instagram

YouTube

Facebook

WhatsApp

TikTok

(Add more in blocked_sites.json)

Pomodoro timer inside the browser

Sessions logged to the same SQLite DB

🏗️ Installation Instructions (Windows)
⚠️ Prerequisites

Python 3.10+

Windows 10/11

Microsoft Visual C++ Build Tools (optional but recommended)

1️⃣ Clone or Download the Project
git clone <your-repo-url>
cd "Pyros - Web Browser"


Or extract the .zip directly.

2️⃣ Create a Virtual Environment

CMD (Recommended)

python -m venv venv
venv\Scripts\activate.bat


PowerShell (If CMD unavailable):

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1

3️⃣ Install Dependencies
pip install -r requirements.txt


If PyQtWebEngine fails, install manually:

pip install PyQt5 PyQtWebEngine

4️⃣ Run the Flask Dashboard
python app.py


Open:

http://127.0.0.1:5000/

5️⃣ Launch the Study Browser

Inside the dashboard, click:

🖱 Open Study Browser

This opens the PyQt browser window.

If it does not open:

Ensure study_browser.py exists

Ensure Python is installed correctly

📁 Folder Structure
Pyros - Web Browser/
│ app.py
│ study_browser.py
│ blocked_sites.json
│ productivity.db
│ quotes.txt
│ requirements.txt
│ README.md
│
├── templates/
│   ├── base.html
│   ├── index.html
│   └── stats.html
│
└── static/
    ├── style.css
    └── timer.js

🔧 Configuration
✔ Customize blocked websites

Edit blocked_sites.json:

[
  "instagram.com",
  "youtube.com",
  "facebook.com",
  "tiktok.com",
  "whatsapp.com"
]

✔ Customize quotes

Add lines to quotes.txt.

🛠️ Troubleshooting
❌ PowerShell cannot activate venv
running scripts is disabled on this system


✔ Fix:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

❌ PyQt WebEngine import error

Install manually:

pip install PyQtWebEngine

❌ “Study Browser not found”

Ensure the file is named:

study_browser.py


Not StudentBrowser.py.

❌ Website blocking not working

Blocking only works during Study Mode.
Click Start Study inside the PyQt Browser window.

🎯 Usage Summary
Start Flask dashboard
python app.py

Open Study Browser

Click → Open Study Browser

Start Pomodoro (Web Dashboard)

Client-side JavaScript timer
(logging is manual via “Log Session Now”)

Start Pomodoro (Browser Window)

Enables automatic site blocking

📦 Packaging for Friends / Other PCs

To make distribution easy:

Option 1: Send ZIP

Include:

Entire project folder

README.md

They only need Python.

Option 2: Convert to EXE (Optional)





📌 Bookmarks inside the Study Browser

Just ask!
