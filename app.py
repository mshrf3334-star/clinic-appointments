from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if request.method == "POST":
        # هنا تحفظ بيانات الموعد لو تبغى
        flash("تم حجز الموعد بنجاح ✅")
        return redirect(url_for("appointments"))
    return render_template("appointment_form.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            flash("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/admin")
def admin_dashboard():
    if "user" in session:
        return render_template("admin_dashboard.html")
    else:
        flash("يلزم تسجيل الدخول أولاً")
        return redirect(url_for("login"))
