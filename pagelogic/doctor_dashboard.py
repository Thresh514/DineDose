from flask import render_template, request

def index():
    res = None
    if request.method == "POST":
        num_str = request.form.get("num")
        if num_str:
            try:
                res = int(num_str) // 2
            except ValueError:
                res = "Invalid input"

    return render_template("doctor_dashboard.html", res=res)

def get_doctor_name(id):
    if id == 20050127:
        return "Zetian"
    return 



