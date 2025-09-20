from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "your_secret_key"

# --- الصفحة الرئيسية ---
@app.route("/")
def index():
    return render_template("index.html")

# --- صفحة الحجز ---
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

        flash("تم حجز الموعد بنجاح ✅", "success")
        return redirect(url_for("book"))

    return render_template("appointment_form.html")

# --- تسجيل الدخول ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "1234":
            session["user"] = "admin"
            return redirect(url_for("admin_dashboard"))
        else:
            flash("اسم المستخدم أو كلمة المرور غير صحيحة ❌", "danger")

    return render_template("login.html")

# --- لوحة الإدارة ---
@app.route("/admin")
def admin_dashboard():
    if "user" not in session:
        flash("يلزم تسجيل الدخول أولاً", "warning")
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)
