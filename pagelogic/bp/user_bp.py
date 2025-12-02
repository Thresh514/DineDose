from flask import Blueprint, request, jsonify, session
from pagelogic.repo import user_repo

user_bp = Blueprint("user", __name__)

@user_bp.route('/get_doctors', methods=['GET'])
def get_doctors_handler():
    """Get doctor by patient_id."""
    patient_id = int(request.args.get("id"))

    doctor = user_repo.get_doctor_by_patient_id(patient_id)
    if doctor is None:
        return jsonify({"error": "doctor_not_found"}), 404

    return jsonify(doctor.to_dict()), 200


@user_bp.route('/get_patients', methods=['GET'])
def get_patients_handler():
    """Get all patients by doctor_id."""
    doctor_id = int(request.args.get("id"))

    patients = user_repo.get_patients_by_doctor_id(doctor_id)
    patient_dicts = [p.to_dict() for p in patients]

    return jsonify(patient_dicts), 200


@user_bp.route('/get_current_user', methods=['GET'])
def get_current_user_handler():
    """Get current logged-in user info."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "not_logged_in"}), 401

    user = user_repo.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "user_not_found"}), 404

    return jsonify(user.to_dict()), 200


@user_bp.route('/update_username', methods=['POST'])
def update_username_handler():
    """Update current user's username."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "not_logged_in"}), 401

    data = request.get_json()
    new_username = data.get('username') if data else None

    if new_username is None:
        return jsonify({"error": "username_required"}), 400

    updated_user = user_repo.update_user_basic_info(user_id, username=new_username)
    if not updated_user:
        return jsonify({"error": "update_failed"}), 500

    return jsonify(updated_user.to_dict()), 200