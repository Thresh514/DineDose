from flask import Blueprint, render_template, request, session
from pagelogic.repo import user_repo
from pagelogic.service import plan_service

doctor_page_bp = Blueprint("doctor_page_bp", __name__)

@doctor_page_bp.route("/doctor/home")
def doctor_patients_page():
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


@doctor_page_bp.route("/doctor/plan_editor", methods=["GET"])
def doctor_plan_editor():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return "Missing patient_id", 400

    plan = plan_service.get_raw_plan(int(patient_id))
    if not plan:
        return "No plan found for this patient", 404
    
    patient = user_repo.get_user_by_id(patient_id)
    patient_name = patient.username if patient else f"Patient {patient_id}"

    return render_template(
        "doctor_plan_editor.html",
        patient_id=patient_id,
        plan=plan.to_dict(),
        patient_name=patient_name,
    )



@doctor_page_bp.route("/doctor/plan_item_create", methods=["GET"])
def doctor_plan_item_create():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return "Missing patient_id", 400

    # 拿到这个 patient 的 plan，为了得到 plan_id
    plan = plan_service.get_user_plan(int(patient_id), None, None)
    if not plan:
        return "No plan found for this patient", 404
    
    patient = user_repo.get_user_by_id(patient_id)
    patient_name = patient.username if patient else f"Patient {patient_id}"
    return render_template(
        "doctor_plan_item_create.html",
        patient_id=patient_id,
        plan_id=plan.id,
        patient_name=patient_name,
    )


@doctor_page_bp.route("/doctor/plan_item_edit", methods=["GET"])
def doctor_plan_item_edit():
    item_id = request.args.get("item_id")
    patient_id = request.args.get("patient_id")

    if not item_id:
        return "Missing item_id", 400
    if not patient_id:
        return "Missing patient_id", 400

    plan = plan_service.get_user_plan(int(patient_id), None, None)
    if not plan:
        return "No plan found for this patient", 404

    patient = user_repo.get_user_by_id(patient_id)
    patient_name = patient.username if patient else f"Patient {patient_id}"

    target = None
    for it in plan.plan_items:
        if it.id == int(item_id):
            target = it
            break

    if not target:
        return "Item not found", 404

    return render_template(
        "doctor_plan_item_edit.html",
        patient_id=patient_id,
        plan_id=plan.id,
        item=target.to_dict(),
        patient_name=patient_name,
    )