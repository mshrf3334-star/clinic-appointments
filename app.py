from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "your_secret_key"

# بيانات تسجيل الدخول (مبدئية)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# الصفحة الرئيسية
@app.route("/")
def index():
    return render_template("index.html")

# صفحة تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["user"] = username
            flash("تم تسجيل الدخول بنجاح ✅", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("خطأ في اسم المستخدم أو كلمة المرور ❌", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

# لوحة الإدارة
@app.route("/admin")
def admin_dashboard():
    if "user" not in session:
        flash("يلزم تسجيل الدخول أولاً ⚠️", "warning")
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")

# تسجيل خروج
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("تم تسجيل الخروج بنجاح ✅", "info")
    return redirect(url_for("index"))

# صفحة حجز المواعيد
@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        clinic = request.form.get("clinic")
        doctor = request.form.get("doctor")
        date = request.form.get("date")
        time = request.form.get("time")
        duration = request.form.get("duration")

        # هنا تحفظ البيانات في قاعدة بيانات أو ملف
        flash(f"تم حجز الموعد بنجاح للمريض {name} مع الدكتور {doctor} 🩺", "success")
        return redirect(url_for("index"))

    return render_template("appointment_form.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
