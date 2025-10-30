from flask import Flask
import config
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth

from pagelogic import (index, login, logout, doctor_home, patient_home)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

mail = Mail(app)
oauth = OAuth(app)

google_creds = config.OAUTH_CREDENTIALS["google"]

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    api_base_url='https://www.googleapis.com/oauth2/v3/',
    client_id=config.OAUTH_CREDENTIALS['google']['client_id'],
    client_secret=config.OAUTH_CREDENTIALS['google']['client_secret'],
    client_kwargs={'scope': 'openid email profile'}
)

login.mail = mail
login.oauth = oauth

@app.route('/' , methods=['GET','POST'])
def index_page():
    return index.index()

@app.route('/login')
def login_page():
    return login.login()

@app.route('/logout', methods=['GET'])
def logout_page():
    return logout.logout()

@app.route('/login/authorize', methods=['GET'])
def oauth_authorize():
    return login.oauth_authorize()

# --- OAuth 登录 ---
@app.route('/login/google', methods=['GET'])
def google_login():
    return login.oauth_login() 

# --- Magic Link 发送邮件 ---
@app.route('/login/magic', methods=['GET','POST'])
def send_magic_link():
    return login.send_magic_link()

@app.route('/magic_login', methods=['GET','POST'])
def magic_login():
    return login.magic_login()

@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    return doctor_home.doctor_home()

@app.route('/patient', methods=['GET', 'POST'])
def patient():
    return patient_home.patient_home()

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)  