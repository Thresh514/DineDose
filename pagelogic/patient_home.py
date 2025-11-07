from flask import render_template, Blueprint

patient_home_bp = Blueprint('patient_home', __name__)


@patient_home_bp.route('/patient', methods=['GET', 'POST'])
def patient_home():
    return render_template('patient_home.html')


@patient_home_bp.route('/patient/reminder', methods=['GET'])
def patient_reminder_page():
    return render_template('patient_reminder.html')


@patient_home_bp.route('/patient/food', methods=['GET'])
def patient_food_page():
    return render_template('patient_food_category_page.html')


@patient_home_bp.route('/patient/plan', methods=['GET'])
def patient_plan_page():
    return "Patient Plan: Coming soon."


@patient_home_bp.route('/patient/calendar', methods=['GET'])
def patient_calendar_page():
    return render_template('patient_calendar.html')