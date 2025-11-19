from flask import Blueprint, request, jsonify, session
from pagelogic.repo import user_repo

user_bp = Blueprint("user", __name__)

@user_bp.route('/get_doctors', methods=['GET'])
def get_doctors_handler():
    """
    给定 patient_id，返回这个 patient 对应的 doctor。
    如果你之后允许多个 doctor，可以改成返回 list。
    """
    patient_id = int(request.args.get("id"))

    doctor = user_repo.get_doctor_by_patient_id(patient_id)
    if doctor is None:
        # 找不到 doctor，就返回 404 或空对象，你自己选。
        return jsonify({"error": "doctor_not_found"}), 404

    return jsonify(doctor.to_dict()), 200


@user_bp.route('/get_patients', methods=['GET'])
def get_patients_handler():
    """
    给定 doctor_id，返回这个 doctor 的所有 patient 列表。
    """
    doctor_id = int(request.args.get("id"))

    patients = user_repo.get_patients_by_doctor_id(doctor_id)
    patient_dicts = [p.to_dict() for p in patients]

    return jsonify(patient_dicts), 200