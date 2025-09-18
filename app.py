from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# إعداد قاعدة البيانات (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# نموذج لجدول العيادة (Clinic)
class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template('index.html')

# صفحة تسجيل الدخول
@app.route('/login')
def login():
    return render_template('login.html')

# صفحة المواعيد
@app.route('/appointments')
def appointments():
    return render_template('appointment_form.html')

# صفحة لوحة الإدارة
@app.route('/admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# 📌 Route جديد لحجز المواعيد (book) حتى يختفي الخطأ
@app.route('/book')
def book():
    return render_template('appointment_form.html')

# تشغيل التطبيق
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # إنشاء الجداول لو ما كانت موجودة
    app.run(host='0.0.0.0', port=10000)
