# app.py
import io
import os
import sys
import subprocess
import sqlite3
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_file, flash
)
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ============================================================
#  FLASK APP CONFIG
# ============================================================
app = Flask(__name__)
app.secret_key = "student-productivity-app-key"  # safe enough for local


# ============================================================
#  DATABASE INITIALIZATION
# ============================================================
DB_PATH = "productivity.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # To-Do table
    c.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)

    # Study Sessions
    c.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            study_minutes INTEGER,
            break_minutes INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()


# ============================================================
#  DB HELPERS
# ============================================================
def get_todos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, text, done FROM todos ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return data

def add_todo(text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO todos (text, done) VALUES (?, 0)", (text,))
    conn.commit()
    conn.close()

def update_todo_done(todo_id, done=True):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE todos SET done=? WHERE id=?", (1 if done else 0, todo_id))
    conn.commit()
    conn.close()

def delete_todo(todo_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM todos WHERE id=?", (todo_id,))
    conn.commit()
    conn.close()

def log_session(study_minutes, break_minutes):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO study_sessions (date, study_minutes, break_minutes) VALUES (?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d"), study_minutes, break_minutes))
    conn.commit()
    conn.close()

def get_study_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM study_sessions", conn)
    conn.close()
    return df


# ============================================================
#  FLASK ROUTES
# ============================================================

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        # Handle new task
        if "new_todo" in request.form:
            text = request.form.get("new_todo", "").strip()
            if text:
                add_todo(text)
                flash("Task added.", "success")
            return redirect(url_for("index"))

        # Handle "log session now" button
        if "log_session" in request.form:
            study = int(request.form.get("study_minutes", 25))
            brk = int(request.form.get("break_minutes", 5))
            log_session(study, brk)
            flash("Study session logged.", "success")
            return redirect(url_for("index"))

    todos = get_todos()
    df = get_study_df()

    total = int(df["study_minutes"].sum()) if not df.empty else 0
    avg = float(df["study_minutes"].mean()) if not df.empty else 0
    sessions = len(df)

    return render_template("index.html",
                           todos=todos,
                           total=total,
                           avg=avg,
                           sessions=sessions)


# TO-DO ROUTES
@app.route("/todo/<int:todo_id>/done", methods=["POST"])
def todo_done(todo_id):
    update_todo_done(todo_id, True)
    flash("Task marked done.", "info")
    return redirect(url_for("index"))

@app.route("/todo/<int:todo_id>/undone", methods=["POST"])
def todo_undone(todo_id):
    update_todo_done(todo_id, False)
    flash("Task marked undone.", "info")
    return redirect(url_for("index"))

@app.route("/todo/<int:todo_id>/delete", methods=["POST"])
def todo_delete(todo_id):
    delete_todo(todo_id)
    flash("Task deleted.", "warning")
    return redirect(url_for("index"))


# ============================================================
#  OPEN THE PYQT BROWSER WINDOW
# ============================================================
@app.route("/open-browser")
def open_browser():
    """
    Opens the PyQt study browser in a new process.
    """
    script_path = os.path.join(os.path.dirname(__file__), "study_browser.py")

    if not os.path.exists(script_path):
        flash("study_browser.py not found.", "danger")
        return redirect(url_for("index"))

    try:
        subprocess.Popen([sys.executable, script_path])
        flash("Study Browser opened.", "success")
    except Exception as e:
        flash("Failed to launch browser: " + str(e), "danger")

    return redirect(url_for("index"))


# ============================================================
#  STATS PAGE + GRAPH
# ============================================================

@app.route("/stats")
def stats():
    df = get_study_df()
    return render_template("stats.html", has_data=not df.empty)


@app.route("/stats/plot.png")
def stats_plot():
    df = get_study_df()

    # No data → blank image
    if df.empty:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "No study data", ha="center", va="center", fontsize=14)
        ax.axis("off")
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")

    df_grouped = df.groupby("date", as_index=False)["study_minutes"].sum()
    df_grouped["date"] = pd.to_datetime(df_grouped["date"])

    fig, ax = plt.subplots(figsize=(8, 4), dpi=120)

    # Modern style
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("white")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    ax.plot(
        df_grouped["date"], df_grouped["study_minutes"],
        marker="o", linewidth=2
    )
    ax.fill_between(
        df_grouped["date"],
        df_grouped["study_minutes"],
        alpha=0.15
    )

    ax.set_title("Daily Study Minutes", fontsize=14)
    ax.set_ylabel("Minutes")

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ============================================================
#  RUN SERVER
# ============================================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
