from flask import render_template

def index():
    return render_template('doctor_dashboard.html')
