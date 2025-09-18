from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

# --- Models ---
class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session["admin"] = admin.username
            return redirect(url_for("dashboard"))
        return "خطأ في تسجيل الدخول"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")

# --- Database Setup ---
@app.route("/init-db")
def init_db():
    with app.app_context():
        db.create_all()
    return "Database initialized ✅"

@app.route("/reset-and-seed")
def reset_and_seed():
    if os.path.exists("data.db"):
        os.remove("data.db")
    with app.app_context():
        db.create_all()
        if not Clinic.query.first():
            db.session.add(Clinic(name="عيادة الباطنية"))
            db.session.add(Clinic(name="عيادة الأسنان"))
        if not Doctor.query.first():
            db.session.add(Doctor(name="د. أحمد"))
            db.session.add(Doctor(name="د. محمد"))
        if not Admin.query.filter_by(username="admin").first():
            admin = Admin(username="admin")
            admin.set_password("admin123")
            db.session.add(admin)
        db.session.commit()
    return "Database reset and seeded ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
