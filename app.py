from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

# إعداد التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecretkey"

# قاعدة البيانات SQLite
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "clinic.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# تعريف الجداول
class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    doctor = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer, nullable=False)

# إنشاء الجداول إذا ماكانت موجودة
with app.app_context():
    db.create_all()

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template("index.html")

# صفحة المواعيد
@app.route('/appointments')
def appointments():
    all_appointments = Appointment.query.all()
    return render_template("appointments.html", appointments=all_appointments)

# صفحة الحجز
@app.route('/book', methods=["GET", "POST"])
def book():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        phone = request.form.get("phone")
        doctor = request.form.get("doctor")
        date = request.form.get("date")
        time = request.form.get("time")
        duration = request.form.get("duration")

        new_appointment = Appointment(
            fullname=fullname,
            phone=phone,
            doctor=doctor,
            date=date,
            time=time,
            duration=duration
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash("تم حجز الموعد بنجاح", "success")
        return redirect(url_for("appointments"))

    return render_template("book.html")

# تسجيل الدخول (مبدئي)
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "1234":
            flash("تم تسجيل الدخول بنجاح", "success")
            return redirect(url_for("index"))
        else:
            flash("بيانات الدخول غير صحيحة", "danger")
    return render_template("login.html")

# تشغيل التطبيق محلياً
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
