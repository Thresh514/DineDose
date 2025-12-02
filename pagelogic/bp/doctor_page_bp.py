from flask import Blueprint, render_template, request, session, jsonify
from pagelogic.repo import user_repo, plan_repo, feedback_repo, drug_record_repo
from pagelogic.service import plan_service
from datetime import date, datetime, timedelta
from utils.llm_api import call_llm_api
from config import mydb

doctor_page_bp = Blueprint("doctor_page_bp", __name__)

@doctor_page_bp.route("/doctor/home")
def doctor_patients_page():
    doctor_id = session.get("user_id")
    return render_template("doctor_home.html", doctor_id=doctor_id)


@doctor_page_bp.route("/doctor/add_patient", methods=["POST"])
def add_patient():
    """Add patient by email. Validates user exists, is verified, and is a patient."""
    doctor_id = session.get("user_id")
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    patient_email = data.get("email") if data else None
    
    if not patient_email:
        return jsonify({"error": "Patient email is required"}), 400
    
    patient = user_repo.get_user_by_email(patient_email)
    if not patient:
        return jsonify({"error": "User not found"}), 404
    
    if not patient.is_verified:
        return jsonify({"error": "User is not verified"}), 400
    
    if patient.role != "patient":
        return jsonify({"error": "User is not a patient"}), 400
    
    existing_patients = user_repo.get_patients_by_doctor_id(doctor_id)
    if any(p.id == patient.id for p in existing_patients):
        return jsonify({"error": "Patient is already your patient"}), 400
    
    existing_plan = plan_repo.get_plan_by_user_id(patient.id)
    if existing_plan:
        if existing_plan.doctor_id != doctor_id:
            return jsonify({"error": "Patient is already assigned to another doctor"}), 400
        return jsonify({"error": "Patient is already your patient"}), 400
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


@doctor_page_bp.route("/doctor/remove_patient", methods=["POST"])
def remove_patient():
    """Remove patient: delete relationship by removing the plan."""
    doctor_id = session.get("user_id")
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    patient_id = data.get("patient_id") if data else None
    
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400
    
    try:
        patient_id = int(patient_id)
    except ValueError:
        return jsonify({"error": "Invalid patient_id"}), 400
    
    plan = plan_repo.get_plan_by_user_id(patient_id)
    if not plan:
        return jsonify({"error": "Patient not found"}), 404
    
    if plan.doctor_id != doctor_id:
        return jsonify({"error": "You don't have permission to remove this patient"}), 403
    
    try:
        plan_items = plan_repo.get_all_plan_items_by_plan_id(plan.id)
        for item in plan_items:
            plan_repo.delete_plan_item_and_rules(item.id)
        conn = mydb()
        cur = conn.cursor()
        cur.execute("DELETE FROM plan WHERE id = %s", (plan.id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"message": "Patient removed successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to remove patient: {str(e)}"}), 500


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

    doctor_id = session.get("user_id")
    if not doctor_id:
        return "Not logged in", 401

    plan = plan_service.get_raw_plan(int(patient_id))
    
    if not plan:
        patient = user_repo.get_user_by_id(int(patient_id))
        patient_name = patient.username if patient else f"Patient {patient_id}"
        doctor = user_repo.get_user_by_id(doctor_id)
        doctor_name = doctor.username if doctor else None
        
        plan = plan_repo.create_plan(
            patient_id=int(patient_id),
            doctor_id=doctor_id,
            name=f"Treatment Plan for {patient_name}",
            description=None,
            doctor_name=doctor_name,
            patient_name=patient_name,
        )
    
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

    doctor_id = session.get("user_id")
    if not doctor_id:
        return "Not logged in", 401

    plan = plan_service.get_user_plan(int(patient_id), None, None)
    
    if not plan:
        raw_plan = plan_service.get_raw_plan(int(patient_id))
        if not raw_plan:
            patient = user_repo.get_user_by_id(int(patient_id))
            patient_name = patient.username if patient else f"Patient {patient_id}"
            doctor = user_repo.get_user_by_id(doctor_id)
            doctor_name = doctor.username if doctor else None
            
            raw_plan = plan_repo.create_plan(
                patient_id=int(patient_id),
                doctor_id=doctor_id,
                name=f"Treatment Plan for {patient_name}",
                description=None,
                doctor_name=doctor_name,
                patient_name=patient_name,
            )
        plan_id = raw_plan.id
    else:
        plan_id = plan.id
    
    patient = user_repo.get_user_by_id(patient_id)
    patient_name = patient.username if patient else f"Patient {patient_id}"
    return render_template(
        "doctor_plan_item_create.html",
        patient_id=patient_id,
        plan_id=plan_id,
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


@doctor_page_bp.route("/doctor/give_feedback", methods=["POST"])
def give_feedback():
    """Doctor writes feedback for patient on a specific date. Supports manual input or AI generation."""
    doctor_id = session.get("user_id")
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    patient_id = data.get("patient_id")
    feedback_date_str = data.get("feedback_date")
    feedback_text = data.get("feedback")
    use_ai = data.get("use_ai", False)
    
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400
    
    if not feedback_date_str:
        return jsonify({"error": "feedback_date is required"}), 400
    
    try:
        feedback_date = date.fromisoformat(feedback_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    plan = plan_repo.get_plan_by_user_id(patient_id)
    if not plan or plan.doctor_id != doctor_id:
        return jsonify({"error": "You don't have permission to give feedback to this patient"}), 403
    
    if use_ai:
        try:
            plan_data = plan_service.get_user_plan(patient_id, feedback_date, feedback_date)
            records = drug_record_repo.get_drug_records_by_date_range(
                user_id=patient_id,
                start=feedback_date,
                end=feedback_date
            )
            
            context_parts = []
            context_parts.append(f"Patient Date: {feedback_date.isoformat()}\n")
            
            plan_items_found = False
            if plan_data and plan_data.plan_items:
                context_parts.append("Medication Plan for the Day:\n")
                for item in plan_data.plan_items:
                    if item.date == feedback_date:
                        plan_items_found = True
                        time_str = item.time.strftime('%H:%M') if item.time else "No time specified"
                        context_parts.append(f"- {item.drug_name or 'Unknown'}: {item.dosage} {item.unit or ''} @ {time_str}\n")
            
            if not plan_items_found:
                context_parts.append("Medication Plan for the Day: No medication plan found for this date.\n")
            
            if records:
                context_parts.append("\nCompletion Records:\n")
                for rec in records:
                    status_map = {"ON_TIME": "On Time", "LATE": "Late", "EARLY": "Early"}
                    status = status_map.get(rec.status, rec.status)
                    time_str = rec.expected_time.strftime('%H:%M') if rec.expected_time else "No time specified"
                    context_parts.append(f"- {rec.expected_date.isoformat()} {time_str}: {status}\n")
            else:
                context_parts.append("\nCompletion Records: No completion records found for this date.\n")
            
            context = "".join(context_parts)
            prompt = f"As a doctor, please generate a concise, professional, and encouraging feedback (100-200 words) based on the patient's medication plan and completion records for the day:\n\n{context}"
            
            system_prompt = "You are a professional doctor who excels at providing encouraging feedback and advice based on patients' medication records. The feedback should be concise, professional, and positive."
            
            llm_result = call_llm_api(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            if llm_result.get("success"):
                feedback_text = llm_result.get("output", "").strip()
                if not feedback_text:
                    return jsonify({"error": "AI generated empty feedback"}), 500
            else:
                return jsonify({"error": f"AI generation failed: {llm_result.get('error', 'Unknown error')}"}), 500
                
        except Exception as e:
            return jsonify({"error": f"Failed to generate AI feedback: {str(e)}"}), 500
    
    if not feedback_text:
        return jsonify({"error": "feedback is required"}), 400
    
    try:
        feedback = feedback_repo.create_or_update_feedback(
            patient_id=int(patient_id),
            doctor_id=doctor_id,
            feedback_date=feedback_date,
            feedback=feedback_text
        )
        
        return jsonify({
            "message": "Feedback saved successfully",
            "feedback": feedback.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to save feedback: {str(e)}"}), 500


@doctor_page_bp.route("/doctor/get_feedback", methods=["GET"])
def get_feedback():
    """Get feedback for patient on a specific date."""
    doctor_id = session.get("user_id")
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401
    
    patient_id = request.args.get("patient_id")
    feedback_date_str = request.args.get("feedback_date")
    
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400
    
    if not feedback_date_str:
        return jsonify({"error": "feedback_date is required"}), 400
    
    try:
        feedback_date = date.fromisoformat(feedback_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    plan = plan_repo.get_plan_by_user_id(patient_id)
    if not plan or plan.doctor_id != doctor_id:
        return jsonify({"error": "You don't have permission to view feedback for this patient"}), 403
    
    feedback = feedback_repo.get_feedback_by_date(int(patient_id), feedback_date)
    
    if feedback:
        return jsonify({"feedback": feedback.to_dict()}), 200
    else:
        return jsonify({"feedback": None}), 200


@doctor_page_bp.route("/doctor/feedback", methods=["GET"])
def doctor_feedback_page():
    """Doctor feedback page: get all patients with plans and their statistics."""
    doctor_id = session.get("user_id")
    if not doctor_id:
        return "Not logged in", 401
    
    patients = user_repo.get_patients_by_doctor_id(doctor_id)
    
    patients_with_stats = []
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    
    for patient in patients:
        plan = plan_repo.get_plan_by_user_id(patient.id)
        if not plan:
            continue
        
        plan_items = plan_repo.get_all_plan_items_by_plan_id(plan.id)
        if not plan_items or len(plan_items) == 0:
            continue
        
        yesterday_plan = plan_service.get_user_plan(patient.id, yesterday, yesterday)
        yesterday_records = drug_record_repo.get_drug_records_by_date_range(
            user_id=patient.id,
            start=yesterday,
            end=yesterday
        )
        
        yesterday_completion = 0
        if yesterday_plan and yesterday_plan.plan_items:
            total_tasks = len(yesterday_plan.plan_items)
            completed_tasks = len([r for r in yesterday_records if r.status == "TAKEN" and r.updated_at])
            if total_tasks > 0:
                yesterday_completion = round((completed_tasks / total_tasks) * 100)
        
        today_plan = plan_service.get_user_plan(patient.id, today, today)
        today_tasks = len(today_plan.plan_items) if today_plan and today_plan.plan_items else 0
        
        if yesterday_completion < 70:
            risk_level = "High"
        elif yesterday_completion < 85:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        feedback = feedback_repo.get_feedback_by_date(patient.id, yesterday)
        has_feedback_today = feedback is not None
        
        patients_with_stats.append({
            "id": patient.id,
            "username": patient.username,
            "email": patient.email,
            "yesterday_completion": yesterday_completion,
            "today_tasks": today_tasks,
            "risk_level": risk_level,
            "has_feedback_today": has_feedback_today
        })
    
    return render_template("doctor_feedback.html", 
                         doctor_id=doctor_id, 
                         patients=patients_with_stats)


@doctor_page_bp.route("/doctor/plans", methods=["GET"])
def doctor_plans_page():
    """Doctor plans page: show all patient plans."""
    doctor_id = session.get("user_id")
    if not doctor_id:
        return "Not logged in", 401
    
    return render_template("doctor_plans.html", doctor_id=doctor_id)


@doctor_page_bp.route("/doctor/patient_stats", methods=["GET"])
def get_patient_stats():
    """Get patient statistics: yesterday completion rate, today's task count, risk level."""
    doctor_id = session.get("user_id")
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401
    
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400
    
    try:
        patient_id = int(patient_id)
    except ValueError:
        return jsonify({"error": "Invalid patient_id"}), 400
    
    plan = plan_repo.get_plan_by_user_id(patient_id)
    if not plan or plan.doctor_id != doctor_id:
        return jsonify({"error": "You don't have permission to view stats for this patient"}), 403
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    yesterday_plan = plan_service.get_user_plan(patient_id, yesterday, yesterday)
    yesterday_records = drug_record_repo.get_drug_records_by_date_range(
        user_id=patient_id,
        start=yesterday,
        end=yesterday
    )
    
    yesterday_completion = 0
    if yesterday_plan and yesterday_plan.plan_items:
        total_tasks = len(yesterday_plan.plan_items)
        completed_tasks = len([r for r in yesterday_records if r.status == "TAKEN" and r.updated_at])
        if total_tasks > 0:
            yesterday_completion = round((completed_tasks / total_tasks) * 100)
    
    today_plan = plan_service.get_user_plan(patient_id, today, today)
    today_tasks = len(today_plan.plan_items) if today_plan and today_plan.plan_items else 0
    
    if yesterday_completion < 70:
        risk_level = "High"
    elif yesterday_completion < 85:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    return jsonify({
        "yesterday_completion": yesterday_completion,
        "today_tasks": today_tasks,
        "risk_level": risk_level
    }), 200