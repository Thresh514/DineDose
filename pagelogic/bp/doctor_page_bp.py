from flask import Blueprint, render_template, request, session, jsonify
from pagelogic.repo import user_repo, plan_repo
from pagelogic.service import plan_service

doctor_page_bp = Blueprint("doctor_page_bp", __name__)

@doctor_page_bp.route("/doctor/home")
def doctor_patients_page():
    doctor_id = session.get("user_id")
    return render_template("doctor_home.html", doctor_id=doctor_id)


@doctor_page_bp.route("/doctor/add_patient", methods=["POST"])
def add_patient():
    """
    通过邮箱添加患者。
    验证：
    1. 用户是否存在
    2. 用户是否已验证（is_verified）
    3. 用户角色是否为patient
    如果都满足，创建plan建立医生和患者的关系。
    """
    doctor_id = session.get("user_id")
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    patient_email = data.get("email") if data else None
    
    if not patient_email:
        return jsonify({"error": "Patient email is required"}), 400
    
    # 1. Check if user exists
    patient = user_repo.get_user_by_email(patient_email)
    if not patient:
        return jsonify({"error": "User not found"}), 404
    
    # 2. Check if user is verified
    if not patient.is_verified:
        return jsonify({"error": "User is not verified"}), 400
    
    # 3. Check if user role is patient
    if patient.role != "patient":
        return jsonify({"error": "User is not a patient"}), 400
    
    # 4. Check if already a patient of this doctor
    existing_patients = user_repo.get_patients_by_doctor_id(doctor_id)
    if any(p.id == patient.id for p in existing_patients):
        return jsonify({"error": "Patient is already your patient"}), 400
    
    # 5. Check if patient already has a plan (possibly with another doctor)
    existing_plan = plan_repo.get_plan_by_user_id(patient.id)
    if existing_plan:
        if existing_plan.doctor_id != doctor_id:
            return jsonify({"error": "Patient is already assigned to another doctor"}), 400
        # If plan is already for current doctor, should be in existing_patients
        return jsonify({"error": "Patient is already your patient"}), 400
    
    # 6. Create plan to establish relationship
    try:
        doctor = user_repo.get_user_by_id(doctor_id)
        doctor_name = doctor.username if doctor else None
        patient_name = patient.username if patient else None
        
        plan_repo.create_plan(
            patient_id=patient.id,
            doctor_id=doctor_id,
            name=f"Treatment Plan for {patient_name or patient_email}",
            description=None,
            doctor_name=doctor_name,
            patient_name=patient_name,
        )
        
        return jsonify({
            "message": "Patient added successfully",
            "patient": {
                "id": patient.id,
                "username": patient.username,
                "email": patient.email,
            }
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to add patient: {str(e)}"}), 500


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