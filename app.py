from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
import os

# =========================
# إعداد التطبيق وقاعدة البيانات
# =========================
app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"  # غيّرها في الإنتاج

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "clinic.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# الموديلات
# =========================
class Appointment(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    phone    = db.Column(db.String(20),  nullable=False)
    clinic   = db.Column(db.String(120))               # التخصص
    doctor   = db.Column(db.String(150), nullable=False)  # اسم الطبيب فقط
    date     = db.Column(db.String(20),  nullable=False)  # YYYY-MM-DD
    time     = db.Column(db.String(20),  nullable=False)  # HH:MM
    duration = db.Column(db.Integer,     nullable=False)  # دقائق

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

# إنشاء الجداول + مستخدم افتراضي
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        u = User(username="admin")
        u.set_password("1234")  # غيّرها بعد أول دخول
        db.session.add(u)
        db.session.commit()

# =========================
# أدوات حماية بسيطة
# =========================
def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            flash("يلزم تسجيل الدخول أولاً", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

# =========================
# الصفحات العامة
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        fullname = request.form.get("name", "").strip()
        phone    = request.form.get("phone", "").strip()
        clinic   = request.form.get("clinic", "").strip()
        doctor   = request.form.get("doctor", "").strip()
        date     = request.form.get("date", "").strip()
        time     = request.form.get("time", "").strip()
        duration = int(request.form.get("duration", "30") or 30)

        if not (fullname and phone and clinic and doctor and date and time):
            flash("رجاءً أكمل كل الحقول المطلوبة", "danger")
            return redirect(url_for("book"))

        appt = Appointment(
            fullname=fullname, phone=phone,
            clinic=clinic, doctor=doctor,
            date=date, time=time, duration=duration
        )
        db.session.add(appt)
        db.session.commit()
        flash("تم حجز الموعد بنجاح ✅", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("appointment_form.html")

# =========================
# تسجيل الدخول/الخروج
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["logged_in"] = True
            session["username"] = user.username
            flash("تم تسجيل الدخول بنجاح", "success")
            return redirect(url_for("admin_dashboard"))
        flash("بيانات الدخول غير صحيحة", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("username", None)
    flash("تم تسجيل الخروج", "info")
    return redirect(url_for("index"))

# =========================
# تغيير كلمة المرور
# =========================
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new     = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        username = session.get("username")
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(current):
            flash("كلمة المرور الحالية غير صحيحة", "danger")
            return redirect(url_for("change_password"))

        if len(new) < 6:
            flash("كلمة المرور الجديدة يجب أن تكون 6 أحرف/أرقام على الأقل", "warning")
            return redirect(url_for("change_password"))

        if new != confirm:
            flash("تأكيد كلمة المرور غير مطابق", "warning")
            return redirect(url_for("change_password"))

        user.set_password(new)
        db.session.commit()
        flash("تم تغيير كلمة المرور بنجاح ✅", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("change_password.html")

# =========================
# لوحة الإدارة + الحذف
# =========================
@app.route("/admin")
@app.route("/admin_dashboard")
@login_required
def admin_dashboard():
    appts = Appointment.query.order_by(Appointment.id.desc()).all()
    return render_template("admin_dashboard.html", appointments=appts)

@app.route("/admin/appointments/<int:appt_id>/delete", methods=["POST"])
@login_required
def delete_appointment(appt_id):
    a = Appointment.query.get_or_404(appt_id)
    db.session.delete(a)
    db.session.commit()
    flash("تم حذف الموعد", "success")
    return redirect(url_for("admin_dashboard"))

# =========================
# هجرة: إضافة عمود clinic + تحويل بيانات قديمة
# =========================
@app.route("/admin/migrate_add_clinic")
@login_required
def migrate_add_clinic():
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE appointment ADD COLUMN clinic VARCHAR(120)"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        updated = 0
        rows = Appointment.query.all()
        for r in rows:
            if (not r.clinic) and r.doctor and "(" in r.doctor and r.doctor.endswith(")"):
                try:
                    name_part = r.doctor.rsplit("(", 1)[0].strip()
                    spec_part = r.doctor.rsplit("(", 1)[1].rstrip(")").strip()
                    if name_part and spec_part:
                        r.doctor = name_part
                        r.clinic = spec_part
                        updated += 1
                except Exception:
                    pass
        if updated:
            db.session.commit()
    return f"Migration done. Updated rows: {updated}"

# =========================
# تشغيل محلي
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
