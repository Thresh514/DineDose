from flask import Flask, request

from pagelogic import signup
from repository.db import db_init
from pagelogic import (index, doctor_dashboard)


app = Flask(__name__)
db = db_init(app) #initialize the connection to the database

@app.route('/' , methods=['GET','POST'])
def index_page():
    return index.index()

@app.route('/doctor', methods=['GET', 'POST'])
def goto_doctor_dashboard():
    return doctor_dashboard.index()

@app.route('/doctor/signup', methods=['POST'])
def create_doctor():
    data = request.get_json()  # 从 body 中获取 JSON 数据
    username = data.get('username')
    email = data.get('email')
    return signup.doctorSignUp(username, email)






if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)  