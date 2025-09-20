# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "replace_this_with_a_strong_secret_key"

# ========== بيانات نموذجية (بدون قاعدة بيانات) ==========
# عيادات
clinics = [
    {"id": "c1", "name": "أسنان"},
    {"id": "c2", "name": "باطنية"},
    {"id": "c3", "name": "مسالك بولية"},
    {"id": "c4", "name": "عظام"},
]

# أطباء (كل طبيب تابع لعيادة برقم id)
doctors = [
    {"id": "d1", "name": "د. أحمد", "clinic_id": "c1", "specialty": "طبيب أسنان"},
    {"id": "d2", "name": "د. سارة", "clinic_id": "c2", "specialty": "أمراض داخلية"},
    {"id": "d3", "name": "د. خالد", "clinic_id": "c3", "specialty": "مسالك بولية"},
    {"id": "d4", "name": "د. ليلى", "clinic_id": "c4", "specialty": "جراحة عظام"},
]

# مواعيد (قائمة كلمات)
appointments = [
    # مثال هيكل:
    # {
    #   "id": "uuid",
    #   "full_name": "علي",
    #   "phone": "+9665xxxx",
    #   "clinic_id": "c1",
    #   "doctor_id": "d1",
    #   "date": "2025-09-25",
    #   "time": "10:30",
    #   "duration": 30,
    #   "created_at": datetime(...)
    # }
]

# بيانات حساب الادمن الافتراضي
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"


# ========== دوال مساعدة ==========
def get_clinic(cid):
    for c in clinics:
        if c["id"] == cid:
            return c
    return None

def get_doctor(did):
    for d in doctors:
        if d["id"] == did:
            return d
    return None

# تحقق من تضارب المواعيد (بسيط: نفس الطبيب والتاريخ والوقت) 
def is_slot_taken(doctor_id, date, time):
    for a in appointments:
        if a["doctor_id"] == doctor_id and a["date"] == date and a["time"] == time:
            return True
    return False


# ========== واجهات الموقع ==========
@app.route("/")
def home():
    # صفحة الاستقبال
    return render_template("index.html")


@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "GET":
        # عرض نموذج الحجز
        return render_template("appointment_form.html", clinics=clinics, doctors=doctors)
    
    # POST: استلام الحقول وحجز
    data = request.form
    full_name = (data.get("full_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    clinic_id = data.get("clinic") or ""
    doctor_id = data.get("doctor") or ""
    date = data.get("date") or ""
    time = data.get("time") or ""
    duration_raw = data.get("duration") or ""
    
    # تحقق الحقول المطلوبة
    missing = []
    if not full_name:
        missing.append("الاسم الكامل")
    if not phone:
        missing.append("رقم الجوال")
    if not clinic_id:
        missing.append("الالعيادة")
    if not doctor_id:
        missing.append("الطبيب")
    if not date:
        missing.append("التاريخ")
    if not time:
        missing.append("الوقت")
    if not duration_raw:
        missing.append("المدة")
    
    if missing:
        flash("يرجى تعبئة الحقول: " + ", ".join(missing))
        return redirect(url_for("book"))
    
    # تأكيد صحة البيانات البسيطة
    try:
        duration = int(duration_raw)
        # تأكد أن العيادة والطبيب موجودين
        if not get_clinic(clinic_id):
            flash("العيادة المختارة غير صالحة")
            return redirect(url_for("book"))
        doc = get_doctor(doctor_id)
        if not doc:
            flash("الطبيب المختار غير صالح")
            return redirect(url_for("book"))
        # تحقق ان الطبيب ينتمي للعيادة
        if doc["clinic_id"] != clinic_id:
            flash("الالعيادة والطيب غير متوافقين")
            return redirect(url_for("book"))
    except ValueError:
        flash("قيمة المدة يجب أن تكون رقمية")
        return redirect(url_for("book"))
    
    # تحقق حجز متضارب
    if is_slot_taken(doctor_id, date, time):
        flash("هذا الموعد غير متاح للطبيب المختار")
        return redirect(url_for("book"))
    
    # انشاء الحجز
    appt = {
        "id": str(uuid.uuid4()),
        "full_name": full_name,
        "phone": phone,
        "clinic_id": clinic_id,
        "doctor_id": doctor_id,
        "date": date,
        "time": time,
        "duration": duration,
        "created_at": datetime.utcnow()
    }
    appointments.append(appt)
    flash("تم حجز الموعد بنجاح ✅")
    return redirect(url_for("home"))


# ========== تسجيل دخول وادارة ==========
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["admin"] = True
        flash("تم تسجيل الدخول كمسؤول")
        return redirect(url_for("admin_dashboard"))
    flash("بيانات دخول خاطئة")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("admin", None)
    flash("تم تسجيل الخروج")
    return redirect(url_for("home"))


@app.route("/admin")
def admin_dashboard():
    if not session.get("admin"):
        flash("عليك تسجيل الدخول كمسؤول")
        return redirect(url_for("login"))
    # رتب المواعيد بحسب تاريخ الإنشاء
    sorted_appts = sorted(appointments, key=lambda x: x["created_at"], reverse=True)
    # أعرض لوحة الإدارة
    # إرسِل بيانات مكملة: اسم العيادة واسم الطبيب
    for a in sorted_appts:
        a["clinic_name"] = get_clinic(a["clinic_id"])["name"] if get_clinic(a["clinic_id"]) else ""
        doc = get_doctor(a["doctor_id"])
        a["doctor_name"] = doc["name"] if doc else ""
        a["doctor_specialty"] = doc["specialty"] if doc else ""
        a["created_str"] = a["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    return render_template("admin_dashboard.html", appointments=sorted_appts)


# صغير: حذف موعد (بواسطة الادمن)
@app.route("/admin/delete/<appt_id>", methods=["POST"])
def admin_delete(appt_id):
    if not session.get("admin"):
        abort(403)
    global appointments
    appointments = [a for a in appointments if a["id"] != appt_id]
    flash("تم حذف الموعد")
    return redirect(url_for("admin_dashboard"))


# صفحة تعاريف بسيطة (اختياري)
@app.context_processor
def inject_common():
    return dict(clinics=clinics, doctors=doctors)


# معالجات أخطاء بسيطة
@app.errorhandler(500)
def server_error(e):
    # لو صار خطأ داخلي نعيد رسالة وداتا للسجل
    app.logger.error("Internal Server Error: %s", e)
    return render_template("500.html", error=e), 500


if __name__ == "__main__":
    # اطبع لو كنت تشغّل محليًا
    print("Starting Flask development server (debug=False)")
    app.run(host="0.0.0.0", port=5000, debug=False)
