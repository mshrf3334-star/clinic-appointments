from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "secret123"

# الصفحة الرئيسية
@app.route("/")
def index():
    return render_template("index.html")

# صفحة الحجز
@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        flash(f"تم حجز الموعد بنجاح للعميل: {name} برقم {phone}")
        return redirect(url_for("appointments"))
    return render_template("appointment_form.html")

# صفحة تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            flash("بيانات الدخول غير صحيحة")
    return render_template("login.html")

# لوحة التحكم
@app.route("/admin")
def admin_dashboard():
    if "user" in session:
        return render_template("admin_dashboard.html")
    else:
        flash("يلزم تسجيل الدخول أولاً")
        return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
