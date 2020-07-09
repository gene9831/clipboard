from flask import Flask, request, render_template, session
import uuid
import os
import time
from threading import Timer, Semaphore
from enum import Enum
import json


app = Flask(__name__, static_folder='static', template_folder='templates')
# 因为vue和render_template的模板都是用{{  }}，所以会冲突，将flask的修改为[[  ]]
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'

app.secret_key = os.urandom(16)


sem = Semaphore()
polling_time = 0.5

clipboard = ''
online_users = {}
lock_owner = None


class RespStatus(Enum):
    SUCCESS = 0
    FAIL = 1
    ERROR = 2


class RespData():
    def __init__(self, status, **kwargs):
        self._status = status
        self._message = status.name.lower()
        self.data = kwargs

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, _status):
        self._status = _status
        self._message = _status.name.lower()

    def add_data(self, **kwargs):
        for k, v in kwargs.items():
            self.data[k] = v

    def to_json(self):
        res = {
            'status': self._status.value,
            'message': self._message
        }
        for k, v in self.data.items():
            if k == 'status' or k == 'message':
                continue

            if isinstance(v, str) or can_convert2json(v):
                res[k] = v

        return json.dumps(res)


def can_convert2json(obj):
    try:
        json.dumps(obj)
    except ValueError:
        return False
    return True


def heartbeat_detect(user):
    if user not in online_users:
        return
    if time.time() - online_users[user] > polling_time * 2:
        online_users.pop(user)

        global lock_owner
        if lock_owner == user:
            sem.acquire()
            lock_owner = None
            sem.release()


@app.route('/')
def home():
    session['user'] = str(uuid.uuid4())
    return render_template('index.html')


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    if 'user' in session:
        online_users[session['user']] = time.time()
        Timer(polling_time * 2, heartbeat_detect, (session['user'],)).start()

        return RespData(RespStatus.SUCCESS,
                        clipboard=clipboard,
                        lock_owner=lock_owner,
                        online_users_num=len(online_users)).to_json()

    return RespData(RespStatus.ERROR).to_json()


@app.route('/acquire_lock')
def acquire_lock():
    res = RespData(RespStatus.FAIL)
    sem.acquire()
    global lock_owner
    if lock_owner is None and 'user' in session:
        lock_owner = session['user']
        res.status = RespStatus.SUCCESS
    sem.release()
    if 'user' not in session:
        res.status = RespStatus.ERROR
    return res.to_json()


@app.route('/release_lock')
def release_lock():
    res = RespData(RespStatus.FAIL)
    sem.acquire()
    global lock_owner
    if lock_owner is not None and 'user' in session and lock_owner == session['user']:
        lock_owner = None
        res.status = RespStatus.SUCCESS
    sem.release()
    if 'user' not in session:
        res.status = RespStatus.ERROR
    return res.to_json()


@app.route('/clipboard', methods=['GET', 'POST'])
def clipboard_content():
    global clipboard
    if request.method == 'GET':
        return RespData(RespStatus.SUCCESS, clipboard=clipboard).to_json()
    else:
        if 'user' in session and session['user'] == lock_owner:
            clipboard = request.form['data']
            return RespData(RespStatus.SUCCESS, clipboard=clipboard).to_json()
        else:
            return RespData(RespStatus.FAIL).to_json()


@app.route('/real_time_data')
def real_time_data():
    res = RespData(RespStatus.SUCCESS)
    res.add_data(clipboard=clipboard,
                 lock_owner=lock_owner,
                 online_users_num=len(online_users),
                 online_users=online_users)
    return res.to_json()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8899)
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8899)
