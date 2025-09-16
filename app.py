from datetime import datetime, timedelta
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ==================
# النماذج (Models)
# ==================
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    clinic = db.relationship('Clinic', backref=db.backref('doctors', lazy=True))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(32), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='booked')  # booked | canceled | completed

    doctor = db.relationship('Doctor')
    patient = db.relationship('Patient')

# ==================
# تسجيل الدخول للأدمن
# ==================
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Admin.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('بيانات الدخول غير صحيحة')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ==================
# صفحات عامة
# ==================
@app.route('/')
def index():
    clinics = Clinic.query.all()
    doctors = Doctor.query.all()
    today = datetime.now().date()
    appts = Appointment.query.filter(Appointment.start_at >= datetime(today.year, today.month, today.day)).order_by(Appointment.start_at).limit(10).all()
    return render_template('index.html', clinics=clinics, doctors=doctors, appts=appts)

@app.route('/book', methods=['GET', 'POST'])
def book():
    clinics = Clinic.query.all()
    doctors = Doctor.query.all()

    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        phone = request.form['phone'].strip()
        doctor_id = int(request.form['doctor_id'])
        date_str = request.form['date']  # YYYY-MM-DD
        time_str = request.form['time']  # HH:MM
        duration = int(request.form.get('duration', 30))  # دقيقة

        start_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        end_at = start_at + timedelta(minutes=duration)

        # إنشاء/إيجاد المريض
        patient = Patient.query.filter_by(phone=phone).first()
        if not patient:
            patient = Patient(full_name=full_name, phone=phone)
            db.session.add(patient)
            db.session.flush()

        # التحقق من التعارض لنفس الطبيب
        conflict = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == 'booked',
            Appointment.start_at < end_at,
            Appointment.end_at > start_at
        ).first()
        if conflict:
            flash('الوقت المطلوب محجوز. اختر وقتًا آخر.')
            return render_template('appointment_form.html', clinics=clinics, doctors=doctors)

        appt = Appointment(doctor_id=doctor_id, patient_id=patient.id, start_at=start_at, end_at=end_at)
        db.session.add(appt)
        db.session.commit()
        flash('تم حجز الموعد بنجاح!')
        return redirect(url_for('index'))

    return render_template('appointment_form.html', clinics=clinics, doctors=doctors)

# ==================
# لوحة التحكم للأدمن
# ==================
@app.route('/admin')
@login_required
def admin_dashboard():
    q = request.args.get('q', '').strip()
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')

    query = Appointment.query
    if doctor_id:
        query = query.filter_by(doctor_id=int(doctor_id))
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(Appointment.start_at >= datetime(d.year, d.month, d.day),
                                 Appointment.start_at < datetime(d.year, d.month, d.day) + timedelta(days=1))
        except Exception:
            pass

    if q:
        query = query.join(Patient).filter(Patient.full_name.contains(q))

    appts = query.order_by(Appointment.start_at.desc()).limit(100).all()
    doctors = Doctor.query.all()
    return render_template('admin_dashboard.html', appts=appts, doctors=doctors)

@app.route('/admin/seed')
@login_required
def admin_seed():
    # إضافة بيانات أولية بسيطة (مرة واحدة)
    if not Clinic.query.first():
        c1 = Clinic(name='الطب العام')
        c2 = Clinic(name='الأسنان')
        db.session.add_all([c1, c2])
        db.session.flush()
        d1 = Doctor(name='د. أحمد', clinic_id=c1.id)
        d2 = Doctor(name='د. سارة', clinic_id=c2.id)
        db.session.add_all([d1, d2])
        db.session.commit()
        flash('تم تهيئة البيانات الأولية للأقسام والأطباء')
    else:
        flash('البيانات مُهيّأة مسبقًا')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/cancel/<int:appt_id>')
@login_required
def cancel_appt(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'canceled'
    db.session.commit()
    flash('تم إلغاء الموعد')
    return redirect(url_for('admin_dashboard'))

# ==================
# التذكيرات (اختياري)
# ==================
client = None
scheduler = None

@app.before_first_request
def setup_scheduler():
    global client, scheduler
    if app.config['REMINDERS_ENABLED'] and app.config['TWILIO_ACCOUNT_SID'] and app.config['TWILIO_AUTH_TOKEN'] and app.config['TWILIO_FROM']:
        client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(send_reminders, 'interval', minutes=5)
        scheduler.start()


def send_reminders():
    if not client:
        return
    now = datetime.now()
    in_24h = now + timedelta(hours=24)
    upcoming = Appointment.query.filter(
        Appointment.status == 'booked',
        Appointment.start_at >= in_24h - timedelta(minutes=5),
        Appointment.start_at < in_24h + timedelta(minutes=5)
    ).all()
    for a in upcoming:
        msg = f"تذكير بموعدك غدًا الساعة {a.start_at.strftime('%H:%M')} مع الطبيب {a.doctor.name}."
        to_num = a.patient.phone
        from_num = app.config['TWILIO_FROM']
        try:
            # لواتساب استخدم: from_=f"whatsapp:{from_num}", to=f"whatsapp:{to_num}"
            client.messages.create(from_=from_num, to=to_num, body=msg)
        except Exception as e:
            print('Twilio error:', e)

# ==================
# أوامر سريعة للتهيئة الأولى
# ==================
@app.cli.command('init-db')
def init_db():
    db.create_all()
    # إنشاء أدمن افتراضي: admin / admin123 (غيّرها)
    if not Admin.query.filter_by(username='admin').first():
        u = Admin(username='admin')
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()
        print('Created default admin: admin / admin123')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
