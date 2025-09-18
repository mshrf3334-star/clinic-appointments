from datetime import datetime

@app.route('/book', methods=['GET', 'POST'])
def book():
    # ... جلب doctors + إضافة عينات كما أرسلته لك سابقًا ...

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        doctor_id = request.form.get('doctor_id')
        date_str = request.form.get('date')        # YYYY-MM-DD
        start_str = request.form.get('start_time') # HH:MM
        end_str = request.form.get('end_time')     # HH:MM

        if not (name and phone and doctor_id and date_str and start_str and end_str):
            flash('من فضلك املأ كل الحقول', 'danger')
            return render_template('appointment_form.html', doctors=doctors)

        try:
            start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            end_dt   = datetime.strptime(f"{date_str} {end_str}",   "%Y-%m-%d %H:%M")
        except ValueError:
            flash('صيغة الوقت/التاريخ غير صحيحة', 'danger')
            return render_template('appointment_form.html', doctors=doctors)

        if end_dt <= start_dt:
            flash('وقت الانتهاء يجب أن يكون بعد وقت البداية', 'danger')
            return render_template('appointment_form.html', doctors=doctors)

        duration_minutes = int((end_dt - start_dt).total_seconds() // 60)

        # خزّن حسب حقولك في الـModel
        appt = Appointment(
            patient_name=name,
            phone="+966" + phone.lstrip('+').lstrip('966'),
            doctor_id=int(doctor_id),
            start_at=start_dt,
            duration_minutes=duration_minutes
        )
        db.session.add(appt)
        db.session.commit()

        flash('تم حجز الموعد بنجاح', 'success')
        return redirect(url_for('appointments'))

    return render_template('appointment_form.html', doctors=doctors)
