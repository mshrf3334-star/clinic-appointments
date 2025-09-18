# ... أعلى الملف: عندك models Doctor, Appointment مفترض موجودة
from sqlalchemy.exc import OperationalError

@app.route('/book', methods=['GET', 'POST'])
def book():
    # تأكد من وجود أطباء، ولو ما فيه أضف عينات
    try:
        doctors = Doctor.query.order_by(Doctor.name).all()
    except OperationalError:
        # لو لسه الجداول ما اننشأت
        db.create_all()
        doctors = []

    if not doctors:
        seed = ['د. محمد العتيبي', 'د. سارة القحطاني', 'د. علي الأحمد']
        for name in seed:
            db.session.add(Doctor(name=name))
        db.session.commit()
        doctors = Doctor.query.order_by(Doctor.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        doctor_id = request.form.get('doctor_id')
        date = request.form.get('date')
        time = request.form.get('time')
        duration = int(request.form.get('duration') or 30)

        if not (name and phone and doctor_id and date and time):
            flash('من فضلك املأ كل الحقول المطلوبة', 'danger')
            return render_template('appointment_form.html', doctors=doctors)

        # احفظ الموعد (ركّب من date+time إلى datetime حسب موديلك)
        # ... منطق الحفظ هنا ...
        flash('تم حجز الموعد بنجاح', 'success')
        return redirect(url_for('appointments'))

    return render_template('appointment_form.html', doctors=doctors)
