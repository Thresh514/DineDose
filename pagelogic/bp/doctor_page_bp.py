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


@doctor_page_bp.route("/doctor/remove_patient", methods=["POST"])
def remove_patient():
    """
    移除患者：删除 doctor 和 patient 之间的关系（删除对应的 plan）
    """
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
    
    # 验证权限：确保这个 patient 确实是当前 doctor 的患者
    plan = plan_repo.get_plan_by_user_id(patient_id)
    if not plan:
        return jsonify({"error": "Patient not found"}), 404
    
    if plan.doctor_id != doctor_id:
        return jsonify({"error": "You don't have permission to remove this patient"}), 403
    
    # 删除 plan（这会删除所有相关的 plan_items 和 plan_item_rules）
    try:
        # 先删除所有 plan_items（会自动删除对应的 plan_item_rules）
        plan_items = plan_repo.get_all_plan_items_by_plan_id(plan.id)
        for item in plan_items:
            plan_repo.delete_plan_item_and_rules(item.id)
        
        # 删除 plan
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
    
    # 如果没有plan，自动创建一个
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

    # 拿到这个 patient 的 plan，为了得到 plan_id
    plan = plan_service.get_user_plan(int(patient_id), None, None)
    
    # 如果没有plan，自动创建一个
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
    """
    医生给患者某一天写反馈
    支持手动输入或AI生成
    """
    doctor_id = session.get("user_id")
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    patient_id = data.get("patient_id")
    feedback_date_str = data.get("feedback_date")
    feedback_text = data.get("feedback")  # 如果提供，直接使用
    use_ai = data.get("use_ai", False)  # 是否使用AI生成
    
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400
    
    if not feedback_date_str:
        return jsonify({"error": "feedback_date is required"}), 400
    
    try:
        feedback_date = date.fromisoformat(feedback_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # 验证医生是否有权限给这个患者写反馈
    plan = plan_repo.get_plan_by_user_id(patient_id)
    if not plan or plan.doctor_id != doctor_id:
        return jsonify({"error": "You don't have permission to give feedback to this patient"}), 403
    
    # 如果使用AI生成反馈
    if use_ai:
        try:
            # 获取患者当天的计划项和完成记录
            plan_data = plan_service.get_user_plan(patient_id, feedback_date, feedback_date)
            records = drug_record_repo.get_drug_records_by_date_range(
                user_id=patient_id,
                start=feedback_date,
                end=feedback_date
            )
            
            # 构建上下文信息
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
            
            # 调用LLM API生成反馈
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
    
    # 如果没有提供反馈文本
    if not feedback_text:
        return jsonify({"error": "feedback is required"}), 400
    
    # 保存反馈
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
    """
    获取患者某一天的反馈
    """
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
    
    # 验证权限
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
    """
    医生反馈页面
    获取所有有 plan 的患者及其统计信息
    """
    doctor_id = session.get("user_id")
    if not doctor_id:
        return "Not logged in", 401
    
    # 获取所有患者
    patients = user_repo.get_patients_by_doctor_id(doctor_id)
    
    # 准备患者数据（只包含有 plan 且有 plan_items 的患者）
    patients_with_stats = []
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    
    for patient in patients:
        # 检查是否有 plan
        plan = plan_repo.get_plan_by_user_id(patient.id)
        if not plan:
            continue
        
        # 检查 plan 是否有 plan_items
        plan_items = plan_repo.get_all_plan_items_by_plan_id(plan.id)
        if not plan_items or len(plan_items) == 0:
            continue
        
        # 计算统计信息
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
        
        # 计算风险等级
        if yesterday_completion < 70:
            risk_level = "High"
        elif yesterday_completion < 85:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # 检查昨天是否已经有 feedback
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
    """
    医生计划列表页面 - 显示所有患者的 plan
    """
    doctor_id = session.get("user_id")
    if not doctor_id:
        return "Not logged in", 401
    
    return render_template("doctor_plans.html", doctor_id=doctor_id)


@doctor_page_bp.route("/doctor/patient_stats", methods=["GET"])
def get_patient_stats():
    """
    获取患者统计信息：昨天的完成率、今天的任务数、风险等级
    """
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
    
    # 验证权限
    plan = plan_repo.get_plan_by_user_id(patient_id)
    if not plan or plan.doctor_id != doctor_id:
        return jsonify({"error": "You don't have permission to view stats for this patient"}), 403
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 1. 计算昨天的完成率
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
    
    # 2. 计算今天的任务数
    today_plan = plan_service.get_user_plan(patient_id, today, today)
    today_tasks = len(today_plan.plan_items) if today_plan and today_plan.plan_items else 0
    
    # 3. 计算风险等级（基于完成率）
    # High: < 70%, Medium: 70-85%, Low: > 85%
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