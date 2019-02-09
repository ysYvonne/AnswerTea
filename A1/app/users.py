from flask import render_template, session, redirect, url_for, request, g, send_from_directory
from app import webapp
import hashlib
from hmac import compare_digest

import mysql.connector

from app.config import db_config

import os

webapp.secret_key = '\x80\xa9s*\x12\xc7x\xa9d\x1f(\x03\xbeHJ:\x9f\xf0!\xb1a\xaa\x0f\xee'

SECRET_KEY = b'pseudo randomly generated secret key'
AUTH_SIZE = 16


def sign(cookie):  # sign(password1)
    h = hashlib.md5()
    h.update(bytes(cookie, 'utf-8'))
    return h.hexdigest().encode('utf-8')


def verify(cookie, sig):
    good_sig = sign(cookie)
    return compare_digest(good_sig, sig)


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.route('/signup', methods=['GET'])
# Display an HTML form that allows users to sign up.
def signup():
    return render_template("users/signup.html",title="New User")


@webapp.route('/signup', methods=['POST'])
# Create a new account and save it in the database.
def signup_save():
    username = request.form.get('username',"")
    password1 = request.form.get('password1',"")
    password2 = request.form.get('password2',"")

    error = False

    if username == "" or password1== "" or password2== "" :
        error=True
        error_msg="Error: All fields are required!"

    elif password1 != password2 :
        error=True
        error_msg="Error: The re-typed password does not match your first entry!"

    else :
        cnx = get_db()
        cursor = cnx.cursor()

        query = '''SELECT * FROM users
                          WHERE username = %s'''
        cursor.execute(query,(username,))
        row = cursor.fetchone()

        if row is not None :
            error=True
            error_msg="Error: User name already exists!"


    if error:
        return render_template("users/signup.html",title="New User",error_msg=error_msg, username=username)

    cnx = get_db()
    cursor = cnx.cursor()

    query = ''' INSERT INTO users (username,password)
                       VALUES (%s, %s)'''

    cursor.execute(query,(username,sign(password1)))
    cnx.commit()

    session['authenticated'] = True

    query = '''SELECT id FROM users
                      WHERE username = %s'''
    cursor.execute(query,(username,))
    row = cursor.fetchone()
    session['username'] = row[0]

    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
    path = os.path.join(ROOT, str(row[0]))
    os.makedirs(path)

    return redirect(url_for('login'))


@webapp.route('/login',methods=['GET'])
# Display an HTML form that allows users to log in.
def login():
    return render_template("users/login.html",title="Log in")


@webapp.route('/login_submit',methods=['POST'])
###################################################
def login_submit():
    username = request.form.get('username',"")
    password = request.form.get('password',"")

    error = False

    if username == "" or password== "" :
        error=True
        error_msg="Error: All fields are required!"

    else :
        cnx = get_db()
        cursor = cnx.cursor()

        query = '''SELECT id, password FROM users
                          WHERE username = %s'''
        cursor.execute(query,(username,))
        row = cursor.fetchone()

        if row is None :
            error=True
            error_msg="Error: User Does not exist!"

        elif not verify(password, bytes(row[1], 'utf-8')) :
            error=True
            error_msg="Error: password does not match!"

    if error :
        return render_template("users/login.html",title="Log in",error_msg=error_msg, username=username)

    session['authenticated'] = True
    session['username'] = row[0]

    return redirect(url_for('user_home'))


@webapp.route('/home', methods=['GET'])
def user_home():
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    users_id = session.get('username')

    cnx = get_db()
    cursor = cnx.cursor()

    query = '''SELECT users_id, filename FROM images
                    WHERE users_id = %s'''
    cursor.execute(query,(users_id,))

    return render_template("images/home.html",title="User Home", cursor=cursor)


@webapp.route('/show/<filename>', methods=['GET'])
def send_image(filename):
    filename_thumb = filename + '_thumbnail.png'
    users_id = session.get('username')
    path = os.path.join(str(users_id), filename_thumb)
    return send_from_directory("images", path)


@webapp.route('/logout',methods=['POST'])
# Clear the session when users want to log out.
def logout():
    session.clear()
    return redirect(url_for('main'))
