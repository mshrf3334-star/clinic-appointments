from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecretkey"

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

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw): self.password_hash = generate_password_hash(raw)
    def check_password(self, raw): return check_password_hash(self.password_hash, raw)

with app.app_context():
    db.create_all()
    # إنشاء أدمن افتراضي (مرة واحدة)
    if not Admin.query.filter_by(username="admin").first():
        u = Admin(username="admin")
        u.set_password("1234")  # غيّرها بعد أول دخول
        db.session.add(u)
        db.session.commit()

# ====== صفحات عامة ======
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

# ====== تسجيل الدخول / الخروج ======
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        user = Admin.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["admin_username"] = user.username
            flash("تم تسجيل الدخول ✅", "success")
            return redirect(url_for("admin_dashboard"))
        flash("بيانات الدخول غير صحيحة", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin_username", None)
    flash("تم تسجيل الخروج", "info")
    return redirect(url_for("index"))

# ====== لوحة الإدارة (محمية) ======
def require_admin():
    if not session.get("admin_username"):
        flash("يلزم تسجيل الدخول أولاً", "warning")
        return False
    return True

@app.route("/admin")
@app.route("/admin_dashboard")
def admin_dashboard():
    if not require_admin():
        return redirect(url_for("login"))
    appts = Appointment.query.order_by(Appointment.id.desc()).all()
    return render_template("admin_dashboard.html", appointments=appts)

# حذف موعد (اختياري)
@app.route("/admin/appointments/<int:appt_id>/delete", methods=["POST"])
def delete_appointment(appt_id):
    if not require_admin():
        return redirect(url_for("login"))
    a = Appointment.query.get_or_404(appt_id)
    db.session.delete(a)
    db.session.commit()
    flash("تم حذف الموعد", "success")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
