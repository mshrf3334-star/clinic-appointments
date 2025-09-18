from datetime import datetime, timedelta
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# ----------------------
# إعداد التطبيق وقاعدة البيانات
# ----------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ----------------------
# النماذج
# ----------------------
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

# ----------------------
# إنشاء الجداول وتهيئة بسيطة عند الإقلاع
# ----------------------
with app.app_context():
    db.create_all()
    if not Clinic.query.first():
        c1 = Clinic(name="الطب العام")
        c2 = Clinic(name="الأسنان")
        db.session.add_all([c1, c2])
        db.session.flush()
        d1 = Doctor(name="د. أحمد", clinic_id=c1.id)
        d2 = Doctor(name="د. سارة", clinic_id=c2.id)
        db.session.add_all([d1, d2])
        db.session.commit()

# ----------------------
# المسارات
# ----------------------
@app.route("/")
def index():
    today = datetime.now().date()
    appts = (
        Appointment.query.filter(Appointment.start_at >= datetime(today.year, today.month, today.day))
        .order_by(Appointment.start_at.asc())
        .limit(10)
        .all()
    )
    return render_template("index.html", appts=appts)

@app.route("/book", methods=["GET", "POST"])
def book():
    clinics = Clinic.query.all()
    doctors = Doctor.query.all()
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        phone = request.form["phone"].strip()
        doctor_id = int(request.form["doctor_id"])
        date_str = request.form["date"]  # YYYY-MM-DD
        time_str = request.form["time"]  # HH:MM
        duration = int(request.form.get("duration", 30))

        start_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        end_at = start_at + timedelta(minutes=duration)

        # مريض (إنشاء/إيجاد)
        patient = Patient.query.filter_by(phone=phone).first()
        if not patient:
            patient = Patient(full_name=full_name, phone=phone)
            db.session.add(patient)
            db.session.flush()

        # تعارض لنفس الطبيب
        conflict = (
            Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.status == "booked",
                Appointment.start_at < end_at,
                Appointment.end_at > start_at,
            )
            .first()
        )
        if conflict:
            flash("الوقت المطلوب محجوز. اختر وقتًا آخر.")
            return render_template("appointment_form.html", clinics=clinics, doctors=doctors)

        appt = Appointment(doctor_id=doctor_id, patient_id=patient.id, start_at=start_at, end_at=end_at)
        db.session.add(appt)
        db.session.commit()
        flash("تم حجز الموعد بنجاح!")
        return redirect(url_for("index"))

    return render_template("appointment_form.html", clinics=clinics, doctors=doctors)

@app.route("/admin")
def admin_dashboard():
    from flask import request
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
def cancel_appt(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "canceled"
    db.session.commit()
    flash("تم إلغاء الموعد")
    return redirect(url_for("admin_dashboard"))

# صفحة تأكيد التشغيل محلياً (اختياري)
@app.route("/health")
def health():
    return "OK", 200

# ----------------------
# تشغيل محلي
# ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
