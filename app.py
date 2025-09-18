from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecretkey"

# قاعدة البيانات SQLite
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "clinic.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ====== الموديلات ======
class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    doctor = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(20), nullable=False)    # YYYY-MM-DD
    time = db.Column(db.String(20), nullable=False)    # HH:MM
    duration = db.Column(db.Integer, nullable=False)   # دقائق

with app.app_context():
    db.create_all()

# ====== الصفحات ======
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        fullname = request.form.get("name", "").strip()
        phone    = request.form.get("phone", "").strip()
        doctor   = request.form.get("doctor", "").strip()
        date     = request.form.get("date", "").strip()
        time     = request.form.get("time", "").strip()
        duration = int(request.form.get("duration", "30"))

        if not (fullname and phone and doctor and date and time):
            flash("رجاءً أكمل كل الحقول المطلوبة", "danger")
            return redirect(url_for("book"))

        appt = Appointment(
            fullname=fullname, phone=phone, doctor=doctor,
            date=date, time=time, duration=duration
        )
        db.session.add(appt)
        db.session.commit()
        flash("تم حجز الموعد بنجاح ✅", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("appointment_form.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # تجريبي
    if request.method == "POST":
        flash("تم تسجيل الدخول (تجريبي).", "info")
        return redirect(url_for("admin_dashboard"))
    return render_template("login.html")

@app.route("/admin")
@app.route("/admin_dashboard")
def admin_dashboard():
    # عرض المواعيد الأحدث أولاً
    appts = Appointment.query.order_by(Appointment.id.desc()).all()
    return render_template("admin_dashboard.html", appointments=appts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
