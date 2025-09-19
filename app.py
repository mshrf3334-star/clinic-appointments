import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

# ---------- إعداد قاعدة البيانات (SQLite) ----------
DB_PATH = os.getenv("DB_PATH", "clinic.db")

def db_connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def db_init():
    with db_connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                clinic TEXT NOT NULL,
                doctor TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                duration INTEGER NOT NULL
            )
        """)
        con.commit()

# نضمن إنشاء الجدول عند تشغيل التطبيق
db_init()

# ---------- المسارات ----------
# الرئيسية → نوجّه للحجز مباشرة (علشان أي url_for('home') يشتغل)
@app.route("/")
def home():
    return redirect(url_for("book"))

# الحجز
@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        phone   = request.form.get("phone", "").strip()
        clinic  = request.form.get("clinic", "").strip()
        doctor  = request.form.get("doctor", "").strip()
        date    = request.form.get("date", "").strip()
        time    = request.form.get("time", "").strip()
        duration= request.form.get("duration", "30").strip()

        if not (name and phone and clinic and doctor and date and time):
            flash("رجاءً أكمل كل الحقول المطلوبة", "danger")
            return redirect(url_for("book"))

        try:
            duration = int(duration)
        except ValueError:
            duration = 30

        with db_connect() as con:
            con.execute(
                "INSERT INTO appointments (name, phone, clinic, doctor, date, time, duration) VALUES (?,?,?,?,?,?,?)",
                (name, phone, clinic, doctor, date, time, duration)
            )
            con.commit()

        flash("تم حجز الموعد بنجاح ✅", "success")
        return redirect(url_for("book"))

    return render_template("appointment_form.html")

# تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "admin" and password == "1234":
            session["user"] = username
            session["logged_in"] = True
            flash("تم تسجيل الدخول بنجاح ✅", "success")
            return redirect(url_for("admin_dashboard"))
        flash("❌ اسم المستخدم أو كلمة المرور غير صحيحة", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

# لوحة الإدارة
@app.route("/admin")
def admin_dashboard():
    if not session.get("logged_in"):
        flash("يلزم تسجيل الدخول أولًا", "warning")
        return redirect(url_for("login"))

    with db_connect() as con:
        rows = con.execute("""
            SELECT id, name, phone, clinic, doctor, date, time, duration
            FROM appointments
            ORDER BY date DESC, time DESC, id DESC
        """).fetchall()
        appointments = [dict(r) for r in rows]

    return render_template("admin_dashboard.html", appointments=appointments)

# تسجيل الخروج
@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج بنجاح", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    # المنفذ 10000 مناسب لـ Render. لو محليًا، ما يضر.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
