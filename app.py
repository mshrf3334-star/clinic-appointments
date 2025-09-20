from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret"  # غيّرها لقيمة قوية

# دالة للتحقق من تسجيل الدخول
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get("user") != "admin":
            flash("يلزم تسجيل الدخول أولاً")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

# الصفحة الرئيسية
@app.route("/")
def index():
    return render_template("index.html")

# صفحة حجز المواعيد
@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        phone = request.form.get("phone", "").strip()
        clinic = request.form.get("clinic", "").strip()
        doctor = request.form.get("doctor", "").strip()
        date = request.form.get("date", "").strip()

        if not fullname or not phone or not clinic or not doctor or not date:
            flash("يرجى تعبئة جميع الحقول")
            return render_template("appointment_form.html")

        # هنا تقدر تخزن البيانات في قاعدة بيانات
        flash("تم حجز الموعد بنجاح ✅")
        return redirect(url_for("index"))

    return render_template("appointment_form.html")

# صفحة تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("يرجى تعبئة جميع الحقول")
            return render_template("login.html")

        # بيانات الدخول الافتراضية
        if username == "admin" and password == "1234":
            session["user"] = "admin"
            flash("تم تسجيل الدخول بنجاح")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("بيانات الدخول غير صحيحة")
            return render_template("login.html")

    return render_template("login.html")

# تسجيل الخروج
@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج")
    return redirect(url_for("login"))

# لوحة الإدارة
@app.route("/admin")
@login_required
def admin_dashboard():
    # هنا مستقبلاً تربط بقاعدة بيانات وتعرض الحجوزات
    return render_template("admin_dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
