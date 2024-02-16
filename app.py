import logging
import string
import traceback
import random
import sqlite3
from datetime import datetime
from flask import * # Flask, g, redirect, render_template, request, url_for
from functools import wraps

app = Flask(__name__)

# These should make it so your Flask app always returns the latest version of
# your HTML, CSS, and JS files. We would remove them from a production deploy,
# but don't change them here.
app.debug = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache"
    return response



def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('db/watchparty.sqlite3')
        db.row_factory = sqlite3.Row
        setattr(g, '_database', db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    print("query_db")
    print(cursor)
    rows = cursor.fetchall()
    print(rows)
    db.commit()
    cursor.close()
    if rows:
        if one: 
            return rows[0]
        return rows
    return None

def new_user():
    name = "Unnamed User #" + ''.join(random.choices(string.digits, k=6))
    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    api_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))
    u = query_db('insert into users (name, password, api_key) ' + 
        'values (?, ?, ?) returning id, name, password, api_key',
        (name, password, api_key),
        one=True)
    return u

def get_user_from_cookie(request):
    user_id = request.cookies.get('user_id')
    password = request.cookies.get('user_password')
    if user_id and password:
        return query_db('select * from users where id = ? and password = ?', [user_id, password], one=True)
    return None

def render_with_error_handling(template, **kwargs):
    try:
        return render_template(template, **kwargs)
    except:
        t = traceback.format_exc()
        return render_template('error.html', args={"trace": t}), 500
    
def validate_api_key(req):
    user_id = req.headers['User-Id']
    api_key = req.headers['Api-Key']
    if user_id and api_key:
        return query_db('select * from users where id = ? and api_key = ?', [user_id, api_key], one=True)
    return None

# ------------------------------ NORMAL PAGE ROUTES ----------------------------------

@app.route('/')
def index():
    print("index") # For debugging
    user = get_user_from_cookie(request)

    if user:
        rooms = query_db('select * from rooms')
        return render_with_error_handling('index.html', user=user, rooms=rooms)
    
    return render_with_error_handling('index.html', user=None, rooms=None)

@app.route('/rooms/new', methods=['GET', 'POST'])
def create_room():
    print("create room") # For debugging
    user = get_user_from_cookie(request)
    if user is None: return {}, 403

    if (request.method == 'POST'):
        name = "Unnamed Room " + ''.join(random.choices(string.digits, k=6))
        room = query_db('insert into rooms (name) values (?) returning id', [name], one=True)            
        return redirect(f'{room["id"]}')
    else:
        return app.send_static_file('create_room.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("signup")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/profile')
        # return render_with_error_handling('profile.html', user=user) # redirect('/')
    
    if request.method == 'POST':
        u = new_user()
        print("u")
        print(u)
        for key in u.keys():
            print(f'{key}: {u[key]}')

        resp = redirect('/profile')
        resp.set_cookie('user_id', str(u['id']))
        resp.set_cookie('user_password', u['password'])
        return resp
    
    return redirect('/login')

@app.route('/profile')
def profile():
    print("profile")
    user = get_user_from_cookie(request)
    if user:
        return render_with_error_handling('profile.html', user=user)
    
    redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("login")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['name']
        u = query_db('select * from users where name = ? and password = ?', [name, password], one=True)
        if user:
            resp = make_response(redirect("/"))
            resp.set_cookie('user_id', u.id)
            resp.set_cookie('user_password', u.password)
            return resp

    return render_with_error_handling('login.html', failed=True)   

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('user_id', '')
    resp.set_cookie('user_password', '')
    return resp

def get_last_msg_id():
    return query_db('select max(id) from messages', [], one=True)

@app.route('/rooms/<int:room_id>')
def room(room_id):
    user = get_user_from_cookie(request)
    if user is None: return redirect('/')

    room = query_db('select * from rooms where id = ?', [room_id], one=True)
    return render_with_error_handling('room.html',
            room=room, user=user)

# -------------------------------- API ROUTES ----------------------------------

# POST to change the user's name
@app.route('/api/user/name', methods=['POST'])
def change_username():
    user = validate_api_key(request)
    if user:
        if request.method == 'POST':
            update_user = query_db('update users set name = ? where api_key = ?', 
                [request.args['user_name'], request.headers['Api-Key']],
                one=True
            )
            response = make_response(redirect('/profile'))
            response.set_cookie('user_id', request.args['user_name'])
            return {}
    else:
        return render_template('error.html', args={"trace: ": 'Invalid User Credentials'}), 401
    return {'Status': 'Something went wrong!!'}, 403

# POST to change the user's password
@app.route('/api/user/password', methods=['POST'])
def change_password():
    user = validate_api_key(request)
    if user:
        if request.method == 'POST':
            update_password = query_db('update users set password = ? where api_key = ?',
                [request.headers['Password'], request.headers['Api-Key']],
                one=True
            )
            password = request.headers['Password']
            resp = make_response({'pass':'Password set successfully!'})
            resp.set_cookie('user_password', password)
            return resp
    else:
        return render_template('error.html', args={"trace: ": 'Invalid User Credentials'}), 401
    return {'Status': 'Something went wrong!!'}, 403


# POST to change the name of a room
@app.route('/api/room/name', methods=['POST'])
def change_room():
    user = validate_api_key(request)
    if user:
        if request.method == 'POST':
            update_room = query_db('update rooms set name = ? where id = ?',
                [request.args['name'], request.args['room_id']],
                one=True
            )
            return {'status': 'Success'}, 200
    else:
        return render_template('error.html', args={"trace: ": 'Invalid User Credentials'}), 401
    return {'Status': 'Something went wrong!!'}, 403

# GET to get all the messages in a room
@app.route('/api/room/messages', methods=['GET'])
def get_chat_messages():
    output = {}
    user = validate_api_key(request)
    if user:
        if request.method == 'GET':
            room_id = request.args['room_id']
            messages = query_db('select msg.id, u.name, msg.body from messages msg, users u '
                        'where msg.room_id = ? and msg.user_id = u.id order by msg.id', [room_id], one=False)
            if not messages:
                return output
            for msg in messages:
                output[msg[0]] = {'id': msg[0], 'name': msg[1], 'body': msg[2]}
        return output, 200
    else:
        return render_template('error.html', args={"trace: ": 'Invalid User Credentials'}), 401
    return {'Status': 'Something went wrong!!'}, 403


# POST to post a new message to a room
@app.route('/api/room/new_msg', methods=['POST'])
def post_message():
    user = validate_api_key(request)
    if user:
        last_msg_id = get_last_msg_id()
        if request.method == 'POST':
            insert_messages = query_db('insert into messages (id, user_id, room_id, body) ' + 'values (?, ?, ?, ?)',
                (int(last_msg_id[0]) + 1, request.headers['User-Id'], request.args['room_id'], request.args['body']), one=True)
            return {'status': 'Success'}, 200
    else:
        return render_template('error.html', args={"trace: ": 'Invalid User Credentials'}), 401
    return {'Status': 'Something went wrong!!'}, 403