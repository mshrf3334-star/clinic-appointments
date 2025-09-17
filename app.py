from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# تعريف الموديل
class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    doctor = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(50), nullable=False)

# إنشاء الجداول إذا ماكانت موجودة
with app.app_context():
    db.create_all()

# الصفحة الرئيسية
@app.route('/')
def index():
    clinics = Clinic.query.all()
    return render_template('index.html', clinics=clinics)

# إضافة موعد
@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    doctor = request.form['doctor']
    time = request.form['time']
    new_clinic = Clinic(name=name, doctor=doctor, time=time)
    db.session.add(new_clinic)
    db.session.commit()
    return redirect(url_for('index'))

# حذف موعد
@app.route('/delete/<int:id>')
def delete(id):
    clinic = Clinic.query.get(id)
    db.session.delete(clinic)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
