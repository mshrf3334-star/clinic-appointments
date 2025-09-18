# app.py
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# ---------------------------------
# إعداد التطبيق والقاعدة
# ---------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clinic.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change-me"

db = SQLAlchemy(app)

# ---------------------------------
# نماذج الجداول
# ---------------------------------
class Clinic(db.Model):
    __tablename__ = "clinic"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class Appointment(db.Model):
    __tablename__ = "appointment"
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    duration_mins = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    clinic = db.relationship("Clinic", backref="appointments")

# ---------------------------------
# تهيئة القاعدة والبيانات الافتراضية
# ---------------------------------
def init_db():
    """إنشاء الجداول وإضافة عيادات افتراضية عند أول تشغيل."""
    db.create_all()
    if Clinic.query.count() == 0:
        db.session.add_all([
            Clinic(name="د. أحمد — باطنية"),
            Clinic(name="د. سارة — عيون"),
            Clinic(name="د. محمد — أسنان")
        ])
        db.session.commit()

# ننفّذ التهيئة داخل سياق التطبيق
with app.app_context():
    init_db()

# ---------------------------------
# الدوال المساعدة
# ---------------------------------
def parse_datetime_from_form(date_str: str, time_str: str) -> datetime:
    """
    يتوقع date بشكل YYYY-MM-DD  و time بشكل HH:MM
    """
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

def has_overlap(clinic_id: int, start_at: datetime, end_at: datetime) -> bool:
    """يتحقق من أي تعارض مع مواعيد نفس العيادة."""
    q = Appointment.query.filter(
        Appointment.clinic_id == clinic_id,
        Appointment.start_at < end_at,
        Appointment.end_at > start_at
    )
    return db.session.query(q.exists()).scalar()

# ---------------------------------
# الصفحات (Routes)
# ---------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/book", methods=["GET", "POST"])
def book():
    clinics = Clinic.query.order_by(Clinic.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        clinic_id = request.form.get("clinic_id")
        date_str = request.form.get("date")
        time_str = request.form.get("time")
        duration = request.form.get("duration", "30").strip()

        # تحقق أساسي من المدخلات
        if not (name and phone and clinic_id and date_str and time_str):
            flash("رجاءً أكمل كل الحقول المطلوبة.", "danger")
            return render_template("appointment_form.html", clinics=clinics)

        try:
            clinic_id = int(clinic_id)
            duration = int(duration or 30)
            start_at = parse_datetime_from_form(date_str, time_str)
            end_at = start_at + timedelta(minutes=duration)
        except Exception:
            flash("صيغة التاريخ/الوقت غير صحيحة.", "danger")
            return render_template("appointment_form.html", clinics=clinics)

        # تعارض المواعيد
        if has_overlap(clinic_id, start_at, end_at):
            flash("هناك تعارض مع موعد آخر لهذه العيادة في نفس الوقت.", "warning")
            return render_template("appointment_form.html", clinics=clinics)

        # حفظ الموعد
        appt = Appointment(
            patient_name=name,
            phone=phone,
            clinic_id=clinic_id,
            start_at=start_at,
            end_at=end_at,
            duration_mins=duration,
        )
        db.session.add(appt)
        db.session.commit()
        flash("تم حجز الموعد بنجاح ✅", "success")
        return redirect(url_for("book"))

    # GET
    return render_template("appointment_form.html", clinics=clinics)

@app.route("/appointments")
def appointments():
    data = (
        Appointment.query
        .order_by(Appointment.start_at.desc())
        .all()
    )
    return render_template("admin_dashboard.html", appointments=data)

@app.route("/login", methods=["GET", "POST"])
def login():
    # واجهة مبدئية (بدون تحقق فعلي). يمكن تطويرها لاحقًا.
    if request.method == "POST":
        flash("تم تسجيل الدخول (تجريبي).", "info")
        return redirect(url_for("appointments"))
    return render_template("login.html")

# صفحة بسيطة للمواعيد حسب العيادة (اختياري)
@app.route("/appointments/clinic/<int:clinic_id>")
def appointments_by_clinic(clinic_id: int):
    clinic = Clinic.query.get_or_404(clinic_id)
    data = (
        Appointment.query
        .filter_by(clinic_id=clinic_id)
        .order_by(Appointment.start_at.desc())
        .all()
    )
    return render_template("admin_dashboard.html", appointments=data, clinic=clinic)

# ---------------------------------
# للتشغيل محليًا
# ---------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
