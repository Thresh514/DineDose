from flask import render_template, request

from config import mydb

def get_doctor_by_id(doctor_id):
    conn = mydb()
    cur = conn.cursor(dictionary=True)  # ✅ 返回字典格式
    query = "SELECT * FROM users WHERE id = %s AND role = 'doctor'"
    cur.execute(query, (doctor_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result


def index():
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        if not doctor_id:
            return render_template('doctor_dashboard.html', doctor=None)
        doctor = get_doctor_by_id(doctor_id)
        return render_template('doctor_dashboard.html', doctor=doctor)
    else:
        return render_template('doctor_dashboard.html', doctor=None)