import os, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret"  # غيّرها لقيمة قوية

DB_PATH = os.environ.get("DB_PATH", "clinic.db")

# --- أدوات قاعدة البيانات ---
def db_conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def db_init():
    with db_conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                phone TEXT NOT NULL,
                clinic TEXT NOT NULL,
                doctor TEXT NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        con.commit()

db_init()

# --- الصفحة الرئيسية ---
@app.route("/")
def index():
    return render_template("index.html")

# --- صفحة الحجز ---
@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        phone    = request.form.get("phone", "").strip()
        clinic   = request.form.get("clinic", "").strip()
        doctor   = request.form.get("doctor", "").strip()
        date     = request.form.get("date", "").strip()

        if not (fullname and phone and clinic and doctor and date):
            flash("يرجى تعبئة جميع الحقول", "danger")
            return render_template("appointment_form.html")

        with db_conn() as con:
            con.execute(
                "INSERT INTO appointments (fullname, phone, clinic, doctor, date, created_at) VALUES (?,?,?,?,?,?)",
                (fullname, phone, clinic, doctor, date, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            con.commit()

        flash("تم حجز الموعد بنجاح ✅", "success")
        return redirect(url_for("book"))

    return render_template("appointment_form.html")

# --- تسجيل الدخول ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("يرجى تعبئة جميع الحقول", "danger")
            return render_template("login.html")

        if username == "admin" and password == "1234":
            session["user"] = "admin"
            flash("تم تسجيل الدخول بنجاح ✅", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("بيانات الدخول غير صحيحة ❌", "danger")
            return render_template("login.html")

    return render_template("login.html")

# --- تسجيل الخروج ---
@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج", "info")
    return redirect(url_for("login"))

# --- لوحة الإدارة: تعرض المواعيد من قاعدة البيانات ---
@app.route("/admin")
def admin_dashboard():
    if session.get("user") != "admin":
        flash("يلزم تسجيل الدخول أولاً", "warning")
        return redirect(url_for("login"))

    with db_conn() as con:
        rows = con.execute("""
            SELECT id, fullname, phone, clinic, doctor, date, created_at
            FROM appointments
            ORDER BY date DESC, created_at DESC, id DESC
        """).fetchall()
        appointments = [dict(r) for r in rows]

    return render_template("admin_dashboard.html", appointments=appointments)

if __name__ == "__main__":
    # Render سيستخدم gunicorn، هذا فقط للتشغيل المحلي
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
