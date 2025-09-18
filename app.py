from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Clinic

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clinic.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "change-this"

db.init_app(app)

# الصفحة الرئيسية
@app.route("/")
def index():
    return render_template("index.html")

# صفحة المواعيد (حجز موعد)
@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        doctor = request.form.get("doctor")
        date = request.form.get("date")
        time = request.form.get("time")
        duration = request.form.get("duration")

        # تقدر تخزن البيانات في DB أو بس تطبعها للتجربة
        flash(f"تم حجز موعد باسم {name} مع {doctor} بتاريخ {date} الساعة {time}")
        return redirect(url_for("book"))
    return render_template("appointment_form.html")

# تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # منطق الدخول
        flash("تم تسجيل الدخول بنجاح ✅ (تجريبي)")
        return redirect(url_for("admin_dashboard"))
    return render_template("login.html")

# لوحة الإدارة
@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=10000)
