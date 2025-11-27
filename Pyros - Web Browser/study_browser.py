# study_browser.py
import sys
import os
import json
import logging
import sqlite3
import subprocess
from datetime import datetime
from urllib.parse import urlparse

try:
    import winreg
except Exception:
    winreg = None

from PyQt5.QtCore import QUrl, QTimer, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QToolBar, QAction,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QInputDialog, QMessageBox, QListWidgetItem, QSpinBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

# Logging
logging.basicConfig(filename="browser_error.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Use the same DB path as Flask app
DB_PATH = "productivity.db"
BLOCKLIST = "blocked_sites.json"
UPLOADED_IMAGE = "/mnt/data/6607dd8a-28a2-4b83-b273-1dd7f3630f61.png"  # optional icon

# ---------- Database helper (for logging sessions if browser triggers them) ----------
class Database:
    def __init__(self, db_name=DB_PATH):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS study_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        study_minutes INTEGER,
                        break_minutes INTEGER
                    )""")
        self.conn.commit()

    def log_session(self, date, study, brk):
        c = self.conn.cursor()
        c.execute("INSERT INTO study_sessions (date, study_minutes, break_minutes) VALUES (?, ?, ?)",
                  (date, study, brk))
        self.conn.commit()

# ---------- Blocking page class ----------
class BlockedPage(QWebEnginePage):
    def __init__(self, should_block_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_block_func = should_block_func

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        try:
            if self.should_block_func(url):
                QMessageBox.warning(None, "Blocked", "This site is blocked during Study Mode!")
                return False
        except Exception as e:
            logging.error(f"Block error: {e}")
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

# ---------- Theme detection ----------
def detect_system_dark_mode():
    try:
        if sys.platform.startswith("win") and winreg is not None:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return val == 0
            except Exception:
                pass
        if sys.platform == "darwin":
            try:
                out = subprocess.check_output(["defaults", "read", "-g", "AppleInterfaceStyle"], stderr=subprocess.STDOUT)
                return b"Dark" in out
            except subprocess.CalledProcessError:
                return False
    except Exception as e:
        logging.error(f"Theme detection error: {e}")
    return False

# ---------- Main Browser Window ----------
class StudentBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Productivity Browser")
        self.resize(1200, 700)

        try:
            if os.path.exists(UPLOADED_IMAGE):
                self.setWindowIcon(QIcon(UPLOADED_IMAGE))
        except Exception:
            pass

        self.db = Database()
        self.blocklist_file = BLOCKLIST
        self.blocked_domains = self.load_blocklist()

        self.study_mode = False
        self.is_break_time = False
        self.work_minutes = 25
        self.break_minutes = 5
        self.seconds_left = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.is_system_dark = detect_system_dark_mode()
        self.init_ui()

    def load_blocklist(self):
        try:
            if not os.path.exists(self.blocklist_file):
                default = ["instagram.com", "youtube.com", "facebook.com", "whatsapp.com", "tiktok.com"]
                with open(self.blocklist_file, "w", encoding="utf-8") as f:
                    json.dump(default, f, indent=2)
                return default
            with open(self.blocklist_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [d.strip().lower() for d in data if isinstance(d, str) and d.strip()]
        except Exception as e:
            logging.error(f"Error loading blocklist: {e}")
            return ["instagram.com", "youtube.com"]

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Toolbar
        nav_bar = QToolBar("Navigation")
        nav_bar.setMovable(False)
        self.addToolBar(nav_bar)

        back_action = QAction("←", self)
        back_action.triggered.connect(self.go_back)
        nav_bar.addAction(back_action)

        forward_action = QAction("→", self)
        forward_action.triggered.connect(self.go_forward)
        nav_bar.addAction(forward_action)

        refresh_action = QAction("⟳", self)
        refresh_action.triggered.connect(self.refresh_page)
        nav_bar.addAction(refresh_action)

        home_action = QAction("🏠", self)
        home_action.triggered.connect(self.go_home)
        nav_bar.addAction(home_action)

        nav_bar.addSeparator()
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.load_url_from_bar)
        nav_bar.addWidget(self.url_bar)

        # Browser view
        self.view = QWebEngineView()
        self.page = BlockedPage(self.is_site_blocked, self)
        self.view.setPage(self.page)
        main_layout.addWidget(self.view)
        self.go_home()

        # Bottom controls (Pomodoro quick controls)
        bottom = QHBoxLayout()
        self.timer_label = QLabel("00:00 (Idle)")
        bottom.addWidget(self.timer_label)

        self.spin_study = QSpinBox()
        self.spin_study.setRange(1, 180)
        self.spin_study.setValue(self.work_minutes)
        bottom.addWidget(QLabel("Study (min):"))
        bottom.addWidget(self.spin_study)

        self.spin_break = QSpinBox()
        self.spin_break.setRange(1, 60)
        self.spin_break.setValue(self.break_minutes)
        bottom.addWidget(QLabel("Break (min):"))
        bottom.addWidget(self.spin_break)

        start_btn = QPushButton("Start Study")
        start_btn.clicked.connect(self.start_study_session)
        bottom.addWidget(start_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_session)
        bottom.addWidget(stop_btn)

        main_layout.addLayout(bottom)

    # Navigation helpers
    def go_home(self):
        self.load_url("https://www.google.com")

    def load_url_from_bar(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if not (text.startswith("http://") or text.startswith("https://")):
            text = "https://" + text
        self.load_url(text)

    def load_url(self, url_str):
        try:
            url = QUrl(url_str)
            self.view.setUrl(url)
            self.url_bar.setText(url_str)
        except Exception as e:
            logging.error(f"Error loading URL {url_str}: {e}")

    def go_back(self):
        self.view.back()

    def go_forward(self):
        self.view.forward()

    def refresh_page(self):
        self.view.reload()

    # Blocking logic
    def is_site_blocked(self, url: QUrl) -> bool:
        if not self.study_mode:
            return False
        try:
            parsed = urlparse(url.toString())
            host = (parsed.netloc or "").lower().replace("www.", "")
            for domain in self.blocked_domains:
                domain = domain.lower().replace("www.", "")
                if host == domain or host.endswith("." + domain) or domain in host:
                    return True
        except Exception as e:
            logging.error(f"Error checking block for url {url.toString()}: {e}")
        return False

    # Pomodoro
    def start_study_session(self):
        try:
            self.work_minutes = int(self.spin_study.value())
            self.break_minutes = int(self.spin_break.value())
            self.is_break_time = False
            self.study_mode = True
            self.seconds_left = self.work_minutes * 60
            self.timer.start(1000)
            self.update_timer_label()
            QMessageBox.information(self, "Study Mode", "Study session started! Distracting sites are now blocked.")
        except Exception as e:
            logging.error(f"Error starting session: {e}")

    def stop_session(self):
        self.timer.stop()
        self.study_mode = False
        self.is_break_time = False
        self.timer_label.setText("00:00 (Idle)")
        QMessageBox.information(self, "Stopped", "Session stopped. Blocking disabled.")

    def update_timer(self):
        try:
            if self.seconds_left > 0:
                self.seconds_left -= 1
                self.update_timer_label()
            else:
                if not self.is_break_time:
                    # log session and start break
                    try:
                        self.db.log_session(datetime.now().strftime("%Y-%m-%d"), self.work_minutes, self.break_minutes)
                    except Exception as e:
                        logging.error(f"DB log error: {e}")
                    self.is_break_time = True
                    self.study_mode = False
                    self.seconds_left = self.break_minutes * 60
                    QMessageBox.information(self, "Break Time", "Study session complete! Break started. Blocking is OFF during break.")
                else:
                    self.timer.stop()
                    self.is_break_time = False
                    self.study_mode = False
                    self.timer_label.setText("00:00 (Idle)")
                    QMessageBox.information(self, "Back to Work", "Break over. You can start a new study session!")
        except Exception as e:
            logging.error(f"Error in update_timer: {e}")

    def update_timer_label(self):
        minutes = self.seconds_left // 60
        seconds = self.seconds_left % 60
        mode_text = "Study" if not self.is_break_time else "Break"
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d} ({mode_text})")

    def closeEvent(self, event):
        try:
            try:
                self.db.conn.close()
            except Exception:
                pass
        finally:
            event.accept()

# Run standalone
def main():
    app = QApplication(sys.argv)
    win = StudentBrowser()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
