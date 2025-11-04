from flask import session, redirect, url_for
import config

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
    return redirect(url_for('index_page'))