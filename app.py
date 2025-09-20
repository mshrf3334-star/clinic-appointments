# app.py
# -*- coding: utf-8 -*-
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session
)

# نحاول استيراد إعدادات وقاعدة البيانات من ملفاتك إن وُجدت
# (config.py, models.py) — ولو ما وُجدت، نستخدم إعدادات افتراضية.
try:
    from config import Config  # يفترض وجود class Config
except Exception:
    class Config:
        SECRET_KEY = "change-me-please"
        SQLALCHEMY_DATABASE_URI = "sqlite:///clinic.db"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        ADMIN_USERNAME = "admin"
        ADMIN_PASSWORD = "1234"

# models.py يجب أن يحتوي على db و الجداول
# Clinic, Doctor, Appointment. لو ما كانت موجودة، نُعرّف بدائل بسيطة.
try:
    from models import db, Clinic, Doctor, Appointment
except Exception:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()

    class Clinic(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(120), nullable=False, unique=True)

    class Doctor(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(120), nullable=False)
        clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
        clinic = db.relationship('Clinic', backref=db.backref('doctors', lazy=True))

    class Appointment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        patient_name = db.Column(db.String(120), nullable=False)
        phone = db.Column(db.String(30), nullable=False)
        clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
        doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
        date = db.Column(db.Date, nullable=False)
        time = db.Column(db.Time, nullable=False)
        duration_min = db.Column(db.Integer, nullable=False, default=20)
        clinic = db.relationship('Clinic')
        doctor = db.relationship('Doctor')


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)

# ربط قاعدة البيانات
db.init_app(app)

def seed_if_empty():
    """إدخال بيانات أولية للعيادات والأطباء إذا كانت قاعدة البيانات فارغة."""
    if Clinic.query.count() == 0:
        clinics = [
            Clinic(name="الأسنان"),
            Clinic(name="الباطنية"),
            Clinic(name="المسالك البولية"),
            Clinic(name="العظام"),
            Clinic(name="العيون"),
        ]
        db.session.add_all(clinics)
        db.session.commit()

    if Doctor.query.count() == 0:
        # نربط أطباء افتراضياً بكل عيادة
        mapping = {
            "الأسنان": ["د. أحمد", "د. ليلى"],
            "الباطنية": ["د. محمد", "د. سارة"],
            "المسالك البولية": ["د. حسين"],
            "العظام": ["د. فارس", "د. عبدالعزيز"],
            "العيون": ["د. ريم"],
        }
        for clinic in Clinic.query.all():
            for dname in mapping.get(clinic.name, []):
                db.session.add(Doctor(name=dname, clinic_id=clinic.id))
        db.session.commit()

# إنشاء الجداول وتشغيل التهيئة داخل سياق التطبيق (بدون before_first_request)
with app.app_context():
    db.create_all()
    seed_if_empty()


# ---------------------------
# المسارات (Routes)
# ---------------------------

@app.route('/')
def index():
    """الصفحة الرئيسية — ترجع index.html"""
    return render_template('index.html')


@app.route('/book', methods=['GET', 'POST'])
def book():
    """نموذج حجز موعد"""
    clinics = Clinic.query.order_by(Clinic.name).all()
    # لو تم اختيار عيادة، نعرض أطباءها (لدعم التبديل عبر نفس الصفحة)
    selected_clinic_id = request.values.get('clinic_id', type=int)
    doctors = Doctor.query.filter_by(clinic_id=selected_clinic_id).all() if selected_clinic_id else []

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        clinic_id = request.form.get('clinic_id', type=int)
        doctor_id = request.form.get('doctor_id', type=int)
        date_str = request.form.get('date', '')
        time_str = request.form.get('time', '')
        duration = request.form.get('duration', type=int)

        if not all([name, phone, clinic_id, doctor_id, date_str, time_str, duration]):
            flash("يرجى تعبئة جميع الحقول", "danger")
            return render_template(
                'appointment_form.html',
                clinics=clinics, doctors=doctors,
                selected_clinic_id=clinic_id,
                form=request.form
            )

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            flash("صيغة التاريخ/الوقت غير صحيحة", "danger")
            return render_template(
                'appointment_form.html',
                clinics=clinics, doctors=doctors,
                selected_clinic_id=clinic_id,
                form=request.form
            )

        appt = Appointment(
            patient_name=name,
            phone=phone,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            date=date_obj,
            time=time_obj,
            duration_min=duration,
        )
        db.session.add(appt)
        db.session.commit()
        flash("تم حجز الموعد بنجاح ✔", "success")
        return redirect(url_for('index'))

    # GET
    return render_template(
        'appointment_form.html',
        clinics=clinics,
        doctors=doctors,
        selected_clinic_id=selected_clinic_id
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل دخول المدير"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == app.config.get("ADMIN_USERNAME", "admin") and password == app.config.get("ADMIN_PASSWORD", "1234"):
            session['is_admin'] = True
            flash("مرحباً بك 👋", "success")
            return redirect(url_for('admin_dashboard'))
        flash("بيانات الدخول غير صحيحة", "danger")
    # ملاحظة: login.html يعرض اسم المستخدم admin وكلمة المرور 1234 كتلميح
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash("تم تسجيل الخروج", "info")
    return redirect(url_for('index'))


@app.route('/admin')
def admin_dashboard():
    """لوحة الإدارة — تتطلب تسجيل دخول"""
    if not session.get('is_admin'):
        flash("يلزم تسجيل الدخول أولاً", "warning")
        return redirect(url_for('login'))

    appts = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    # نبني بيانات جاهزة للعرض
    rows = []
    for a in appts:
        rows.append({
            "id": a.id,
            "patient_name": a.patient_name,
            "phone": a.phone,
            "clinic": a.clinic.name if a.clinic else "-",
            "doctor": a.doctor.name if a.doctor else "-",
            "date": a.date.strftime("%Y-%m-%d"),
            "time": a.time.strftime("%H:%M"),
            "duration": a.duration_min,
        })
    return render_template('admin_dashboard.html', appointments=rows)


# ---------------------------
# معالجات الأخطاء
# ---------------------------

@app.errorhandler(404)
def not_found(_e):
    # لو ما فيه قالب 404.html، نرجع نص بسيط
    try:
        return render_template('404.html'), 404
    except Exception:
        return "404 - الصفحة غير موجودة", 404


@app.errorhandler(500)
def server_error(_e):
    # السبب الشائع عندك سابقاً: TemplateNotFound لـ 500.html — نعالجه نصياً عند عدم وجود القالب
    try:
        return render_template('500.html'), 500
    except Exception:
        return "حدث خطأ داخلي في الخادم (500).", 500


# لتشغيل محلياً فقط
if __name__ == '__main__':
    app.run(debug=True)
