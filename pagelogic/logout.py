from flask import session, redirect, url_for, Blueprint
import config

logout_bp = Blueprint('logout', __name__)


@logout_bp.route('/logout', methods=['GET'])
def logout():
    token = session.get('session_token')
    if token:
        conn = config.mydb()
        cur = config.cursor(conn)
        cur.execute("DELETE FROM sessions WHERE session_token = %s", (token,))
        conn.commit()
        cur.close()
        conn.close()
    session.clear()
    return redirect(url_for('index.index'))