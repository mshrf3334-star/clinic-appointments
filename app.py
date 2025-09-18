from datetime import datetime, timedelta
import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

# --------------------------------
# إعداد التطبيق و قاعدة البيانات
# --------------------------------
app = Flask(__name__)
app.config.from_object("config.Config")  # يتوقع ملف config.py موجود
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# --------------
# النماذج Models
# --------------
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=False)
    clinic = db.relationship("Clinic", backref=db.backref("doctors", lazy=True))


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(32), nullable=False)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="booked")  # booked | canceled | completed

    doctor = db.relationship("Doctor")
    patient = db.relationship("Patient")


# --------------
# تسجيل الدخول
# --------------
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    # يطابق url_for('login') في القوالب
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = Admin.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin_dashboard"))
        flash("بيانات الدخول غير صحيحة", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# --------------
# صفحات عامة
# --------------
@app.route("/")
def index():
    clinics = Clinic.query.all()
    doctors = Doctor.query.all()
    today = datetime.now().date()
    appts = (
        Appointment.query.filter(
            Appointment.start_at >= datetime(today.year, today.month, today.day)
        )
        .order_by(Appointment.start_at)
        .limit(10)
        .all()
    )
    return render_template("index.html", clinics=clinics, doctors=doctors, appts=appts)


@app.route("/book", methods=["GET", "POST"])
def book():
    clinics = Clinic.query.all()
    doctors = Doctor.query.all()

    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        phone = request.form["phone"].strip()
        doctor_id = int(request.form["doctor_id"])
        date_str = request.form["date"]   # YYYY-MM-DD
        time_str = request.form["time"]   # HH:MM
        duration = int(request.form.get("duration", 30))

        start_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        end_at = start_at + timedelta(minutes=duration)

        patient = Patient.query.filter_by(phone=phone).first()
        if not patient:
            patient = Patient(full_name=full_name, phone=phone)
            db.session.add(patient)
            db.session.flush()

        # منع التعارض
        conflict = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "booked",
            Appointment.start_at < end_at,
            Appointment.end_at > start_at,
        ).first()
        if conflict:
            flash("الوقت المطلوب محجوز. اختر وقتًا آخر.", "error")
            return render_template("appointment_form.html", clinics=clinics, doctors=doctors)

        appt = Appointment(
            doctor_id=doctor_id,
            patient_id=patient.id,
            start_at=start_at,
            end_at=end_at,
        )
        db.session.add(appt)
        db.session.commit()
        flash("تم حجز الموعد بنجاح!", "success")
        return redirect(url_for("index"))

    return render_template("appointment_form.html", clinics=clinics, doctors=doctors)


# --------------
# لوحة التحكم
# --------------
@app.route("/admin")
@login_required
def admin_dashboard():
    q = request.args.get("q", "").strip()
    doctor_id = request.args.get("doctor_id")
    date = request.args.get("date")

    query = Appointment.query
    if doctor_id:
        query = query.filter_by(doctor_id=int(doctor_id))
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(
                Appointment.start_at >= datetime(d.year, d.month, d.day),
                Appointment.start_at < datetime(d.year, d.month, d.day) + timedelta(days=1),
            )
        except Exception:
            pass
    if q:
        query = query.join(Patient).filter(Patient.full_name.contains(q))

    appts = query.order_by(Appointment.start_at.desc()).limit(100).all()
    doctors = Doctor.query.all()
    return render_template("admin_dashboard.html", appts=appts, doctors=doctors)


@app.route("/admin/cancel/<int:appt_id>")
@login_required
def cancel_appt(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "canceled"
    db.session.commit()
    flash("تم إلغاء الموعد", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/seed")
@login_required
def admin_seed():
    # تهيئة بيانات بسيطة
    if not Clinic.query.first():
        c1 = Clinic(name="الطب العام")
        c2 = Clinic(name="الأسنان")
        db.session.add_all([c1, c2])
        db.session.flush()
        d1 = Doctor(name="د. أحمد", clinic_id=c1.id)
        d2 = Doctor(name="د. سارة", clinic_id=c2.id)
        db.session.add_all([d1, d2])
        db.session.commit()
        flash("تم تهيئة البيانات الأولية", "success")
    else:
        flash("البيانات مُهيّأة مسبقًا", "info")
    return redirect(url_for("admin_dashboard"))


# ------------------------
# إنشاء الجداول لأول مرة
# ------------------------
@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not Admin.query.filter_by(username="admin").first():
        u = Admin(username="admin")
        u.set_password("admin123")  # غيّرها بعد الدخول
        db.session.add(u)
        db.session.commit()
        print("Created default admin: admin / admin123")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # إنشاء حساب أدمن افتراضي إن لم يوجد
        if not Admin.query.filter_by(username="admin").first():
            u = Admin(username="admin")
            u.set_password("admin123")
            db.session.add(u)
            db.session.commit()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
