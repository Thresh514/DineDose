from flask import render_template, request, redirect, session, url_for, flash
from authlib.integrations.flask_client import OAuth
import secrets, config
from app import mail, oauth
from itsdangerous import URLSafeTimedSerializer
from pagelogic import doctor_home, patient_home
from utils.emailsender import send_email_ses

s = URLSafeTimedSerializer(config.SECRET_KEY)

def login():
    if session.get('type'):
        return redirect_by_role(session['type'])
    return render_template("login.html")

# Magic Link 登录
def send_magic_link():
    email = request.form['email']
    token = s.dumps(email, salt='magic-login')
    link = url_for('magic_login', token=token, _external=True)

    subject = "Your Magic Login Link"
    html_body = f"""
    <h3>Welcome to DineDose!</h3>
    <p>Click <a href="{link}">here</a> to log in. This link expires in 10 minutes.</p>
    <p> Do not share this link with others.</p>
    <p>If you didn’t request this, please ignore this email.</p>
    """

    if send_email_ses(email, subject, html_body):
        flash("✅ Magic link sent to your email!", "info")
    else:
        flash("❌ Failed to send email.", "error")

    return redirect(url_for('login_page'))

def magic_login():
    token = request.args.get('token')
    try:
        email = s.loads(token, salt='magic-login', max_age=600)
    except Exception:
        flash('Invalid or expired link', 'error')
        return redirect(url_for('login_page'))

    mydb = config.mydb()
    cur = config.cursor(mydb)
    cur.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cur.fetchone()

    # 自动注册
    if not user:
        cur.execute('INSERT INTO users (email, role, is_verified) VALUES (%s, %s, TRUE)', (email, 'patient'))
        mydb.commit()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()

    session.update({
        'type': user.get('role', 'patient'),
        'email': email,
        'session_token': secrets.token_hex(16)
    })
    cur.execute(
        "INSERT INTO sessions (user_id, session_token, user_agent, ip_address) VALUES (%s,%s,%s,%s)",
        (user['id'], session['session_token'], request.headers.get('User-Agent'), request.remote_addr)
    )
    mydb.commit()
    flash('登录成功', 'success')
    return redirect_by_role(user['role'])

# Google OAuth 登录
def oauth_login():
    redirect_uri = url_for('oauth_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

def oauth_authorize():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.get('userinfo').json()
    email = user_info['email']
    name = user_info['name']
    picture = user_info.get('picture')
    google_id = user_info['id'] if 'id' in user_info else user_info['sub']

    mydb = config.mydb()
    cur = config.cursor(mydb)
    cur.execute('SELECT * FROM users WHERE google_id = %s OR email = %s', (google_id, email))
    user = cur.fetchone()

    if not user:
        cur.execute("""
            INSERT INTO users (username, email, google_id, avatar_url, role, is_verified)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """, (name, email, google_id, picture, 'patient'))
        mydb.commit()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()

    session.update({
        'type': user['role'],
        'email': user['email'],
        'name': user['username'],
        'session_token': secrets.token_hex(16)
    })
    cur.execute(
        "INSERT INTO sessions (user_id, session_token, user_agent, ip_address) VALUES (%s,%s,%s,%s)",
        (user['id'], session['session_token'], request.headers.get('User-Agent'), request.remote_addr)
    )
    mydb.commit()
    return redirect_by_role(user['role'])

def redirect_by_role(role):
    if role == 'doctor':
        return doctor_home.doctor_home()
    elif role == 'patient':
        return patient_home.patient_home()
    return redirect(url_for('index_page'))
