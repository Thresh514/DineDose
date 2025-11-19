from flask import Blueprint, render_template, request, session

doctor_page_bp = Blueprint("doctor_page_bp", __name__)

@doctor_page_bp.route("/doctor/home")
def doctor_patients_page():
    """
    医生主页：展示所有自己的 patient（前端用 JS 调 /get_patients）
    """
    # doctor 自己的 id 一般存在 session 里
    doctor_id = session.get("user_id")
    return render_template("doctor_home.html", doctor_id=doctor_id)


@doctor_page_bp.route("/doctor/patient_plan")
def doctor_view_patient_plan():
    patient_id = request.args.get("id")
    patient_name = request.args.get("name", "Unknown")
    patient_email = request.args.get("email", "")

    return render_template(
        "doctor_calendar_view.html",
        patient_id=patient_id,
        patient_name=patient_name,
        patient_email=patient_email,
    )