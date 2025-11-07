from flask import render_template, Blueprint

doctor_home_bp = Blueprint('doctor_home', __name__)


@doctor_home_bp.route('/doctor', methods=['GET', 'POST'])
def doctor_home():
    return render_template('doctor_home.html')