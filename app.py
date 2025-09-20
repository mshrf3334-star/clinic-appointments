# app.py  (نسخة ثابتة ومتكاملة)

from datetime import datetime
import os
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy

# ------------------------
# إعداد التطبيق وقاعدة البيانات
# ------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

# SQLite ملف محلي داخل مجلد المشروع على Render
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///db.sqlite3"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ------------------------
# النماذج (جداول قاعدة البيانات)
# ------------------------
class Clinic(db.Model):
    __tablename__ = "clinic"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    doctors = db.relationship("Doctor", backref="clinic", lazy=True)

class Doctor(db.Model):
    __tablename__ = "doctor"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=False)

class Appointment(db.Model):
    __tablename__ = "appointment"
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    duration_min = db.Column(db.Integer, nullable=False, default=30)

    clinic = db.relationship("Clinic", lazy=True)
    doctor = db.relationship("Doctor", lazy=True)

# ------------------------
# تهيئة الجداول + بيانات افتراضية
# ------------------------
def seed_data():
    """إضافة عيادات وأطباء افتراضيين عند أول تشغيل."""
    if Clinic.query.count() == 0:
        clinics = [
            Clinic(name="الأسنان"),
            Clinic(name="الباطنية"),
            Clinic(name="المسالك البولية"),
            Clinic(name="العظام"),
            Clinic(name="الأنف والأذن"),
        ]
        db.session.add_all(clinics)
        db.session.commit()

        doctors = [
            Doctor(name="د. أحمد", clinic_id=Clinic.query.filter_by(name="الأسنان").first().id),
            Doctor(name="د. سارة", clinic_id=Clinic.query.filter_by(name="الأسنان").first().id),
            Doctor(name="د. محمد", clinic_id=Clinic.query.filter_by(name="الباطنية").first().id),
            Doctor(name="د. نوف", clinic_id=Clinic.query.filter_by(name="المسالك البولية").first().id),
            Doctor(name="د. خالد", clinic_id=Clinic.query.filter_by(name="العظام").first().id),
            Doctor(name="د. ليلى", clinic_id=Clinic.query.filter_by(name="الأنف والأذن").first().id),
        ]
        db.session.add_all(doctors)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

# ------------------------
# مساعدات
# ------------------------
def login_required():
    if "user" not in session:
        flash("⚠️ يرجى تسجيل الدخول أولاً")
        return False
    return True

def admin_ok(username, password):
    # يمكن تغييرها عبر متغيرات البيئة على Render
    u = os.environ.get("ADMIN_USER", "admin")
    p = os.environ.get("ADMIN_PASS", "1234")
    return username == u and password == p

# ------------------------
# الصفحات
# ------------------------

# الصفحة الترحيبية
@app.route("/")
def index():
    return render_template("index.html")

# صفحة الحجز (رابطها /book) — GET لعرض النموذج، POST لحفظ الموعد
@app.route("/book", methods=["GET", "POST"])
def book():
    clinics = Clinic.query.order_by(Clinic.name).all()
    doctors = Doctor.query.order_by(Doctor.name).all()

    if request.method == "POST":
        patient_name = request.form.get("patient_name", "").strip()
        phone = request.form.get("phone", "").strip()
        clinic_id = request.form.get("clinic_id")
        doctor_id = request.form.get("doctor_id")
        date_str = request.form.get("date")          # صيغة: YYYY-MM-DD
        time_str = request.form.get("time")          # صيغة: HH:MM
        duration = int(request.form.get("duration", "30"))

        # تحقق بسيط
        if not (patient_name and phone and clinic_id and doctor_id and date_str and time_str):
            flash("❌ يرجى تعبئة جميع الحقول")
            return redirect(url_for("book"))

        try:
            start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash("❌ صيغة التاريخ/الوقت غير صحيحة")
            return redirect(url_for("book"))

        appt = Appointment(
            patient_name=patient_name,
            phone=phone,
            clinic_id=int(clinic_id),
            doctor_id=int(doctor_id),
            start_time=start_time,
            duration_min=duration,
        )
        db.session.add(appt)
        db.session.commit()

        flash("✅ تم حجز الموعد بنجاح")
        return redirect(url_for("book"))

    # GET
    return render_template(
        "appointment_form.html",
        clinics=clinics,
        doctors=doctors
    )

# API صغيرة لإرجاع أطباء العيادة (تستخدمها الواجهة عبر JS إن رغبت)
@app.route("/api/doctors")
def api_doctors():
    clinic_id = request.args.get("clinic_id", type=int)
    q = Doctor.query
    if clinic_id:
        q = q.filter_by(clinic_id=clinic_id)
    rows = q.order_by(Doctor.name).all()
    return jsonify([{"id": d.id, "name": d.name} for d in rows])

# تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if admin_ok(username, password):
            session["user"] = username
            flash("✅ تم تسجيل الدخول")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
            return redirect(url_for("login"))
    return render_template("login.html")

# لوحة الإدارة
@app.route("/admin_dashboard")
def admin_dashboard():
    if not login_required():
        return redirect(url_for("login"))

    appts = (
        Appointment.query
        .order_by(Appointment.start_time.desc())
        .all()
    )
    stats = {
        "clinics": Clinic.query.count(),
        "doctors": Doctor.query.count(),
        "appointments": Appointment.query.count(),
    }
    return render_template("admin_dashboard.html", appts=appts, stats=stats)

# تسجيل الخروج
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("تم تسجيل الخروج")
    return redirect(url_for("login"))

# فحص صحة الخدمة
@app.route("/healthz")
def healthz():
    return "ok", 200

# معالجة 404 بتحويل لطيفة
@app.errorhandler(404)
def not_found(e):
    return redirect(url_for("index"))

# ------------------------
# تشغيل محلي
# ------------------------
if __name__ == "__main__":
    # على Render سيُشغَّل عبر gunicorn (لا حاجة لتغيير شيء)
    app.run(host="0.0.0.0", port=5000, debug=True)
