from flask import Flask, request, render_template, session
import uuid
import os
import time
from threading import Timer, Semaphore
from enum import IntEnum


app = Flask(__name__, static_folder='static', template_folder='templates')
# 因为vue和render_template的模板都是用{{  }}，所以会冲突，将flask的修改为[[  ]]
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'

app.secret_key = os.urandom(16)


sem = Semaphore()
detect_sec = 1

clipboard = {'clipboard': ''}
online_users = {}
lock_owner = None


class RespStatus(IntEnum):
    SUCCESS = 0
    FAIL = 1
    ERROR = 2


@app.route('/')
def home():
    session['user'] = str(uuid.uuid4())
    return render_template('index.html')


def is_online(user):
    if user not in online_users:
        return
    if time.time() - online_users[user] > detect_sec:
        online_users.pop(user)

        global lock_owner
        if lock_owner == user:
            sem.acquire()
            lock_owner = None
            sem.release()


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    if 'user' in session:
        online_users[session['user']] = time.time()
        Timer(detect_sec, is_online, (session['user'],)).start()
        return {'user': session['user']}
    return {'user': None}


@app.route('/acquire_lock')
def acquire_lock():
    res = {'status': RespStatus.FAIL}
    sem.acquire()
    global lock_owner
    if lock_owner is None and 'user' in session:
        lock_owner = session['user']
        res['status'] = RespStatus.SUCCESS
    sem.release()
    if 'user' not in session:
        res['status'] = RespStatus.ERROR
    return res


@app.route('/release_lock')
def release_lock():
    res = {'status': RespStatus.FAIL}
    sem.acquire()
    global lock_owner
    if lock_owner is not None and 'user' in session and lock_owner == session['user']:
        lock_owner = None
        res = {'status': RespStatus.SUCCESS}
    sem.release()
    if 'user' not in session:
        res['status'] = RespStatus.ERROR
    return res


@app.route('/clipboard', methods=['GET', 'POST'])
def clipboard_content():
    if request.method == 'GET':
        return clipboard
    else:
        if 'user' in session and session['user'] == lock_owner:
            clipboard['clipboard'] = request.form['data']
            status = RespStatus.SUCCESS
        else:
            status = RespStatus.FAIL
        return {
            'status': status,
            'clipboard': clipboard['clipboard'],
        }


@app.route('/real_time_data')
def real_time_data():
    return {
        'clipboard': clipboard['clipboard'],
        'lock_owner': lock_owner,
        'online_users_num': len(online_users)
    }


if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=8899)
    from waitress import serve
    serve(app, host="0.0.0.0", port=8899)
